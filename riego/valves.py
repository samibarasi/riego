from datetime import datetime
import re
import json
from sqlite3 import IntegrityError, Row
from typing import Any

bool_to_int = {'true': 1, 'false': 0, True: 1, False: 0,
               'True': 1, 'False': 0, 'on': 1, 'off': 0,
               'On': 1, 'Off': 0, 'ON': 1, 'OFF': 0}

int_to_js_bool = {1: "true", 0: "false", -1: "-1"}


async def ws_handler(msg: dict) -> None:
    print(f'In ws_handler: {msg}')
    # self._log.debug(f'In Valves._ws_handler: {msg}')
    if msg['action'] == 'update':
        pass
        # await self._update_by_key(msg['id'], msg['key'], msg['value'])
    return None


class Valves():
    def __init__(self, app):
        self._db_conn = app['db'].conn
        self._mqtt = app['mqtt']
        self._log = app['log']
        self._event_log = app['event_log']
        self._options = app['options']
        self._websockets = app['websockets']

        self.__is_running = None

        self._websockets.subscribe('valves', self._ws_handler)
        self._mqtt.subscribe(self._options.mqtt_result_subscription,
                             self._mqtt_result_handler)

    async def _ws_handler(self, msg: dict) -> None:
        self._log.debug(f'In Valves._ws_handler: {msg}')
        if msg['action'] == 'update':
            await self._update_by_key(msg['id'], msg['key'], msg['value'])
        return None

    async def _update_by_key(self, id: int, key: str, value: Any) -> None:
        valve = await self.fetch_one_by_id(id)
        if key == "is_running":
            if bool_to_int.get(value, 0):
                await self._set_on_try(valve)
            else:
                await self._set_off_try(valve)
        else:
            # TODO Data Typ Conversion possible needed
            sql = f'UPDATE valves SET {key} = ? WHERE id = ?'
            with self._db_conn:
                self._db_conn.execute(sql, (value, id))
        valve = await self.fetch_one_by_id(id)
        await self._send_status_with_websocket(valve, key)
        return None

    async def _mqtt_result_handler(self, topic: str, payload: str) -> bool:
        """Dispatch mqtt message "stat/box_name/RESULT {POWER1 :  ON}"

        :param topic: Topic of subscribed MQTT-message
        :type topic: str
        :param payload: Payload of subscribed MQTT-message
        :type payload: str
        :return: [description]
        :rtype: bool
        """
        box_topic = re.search('/(.*?)/', topic)
        if box_topic is None:
            return False
        box_topic = box_topic.group(1)
        payload = json.loads(payload)
        for item in payload:
            valve_topic = f'{box_topic}/{item}'
            valve = await self.fetch_one_by_key("topic", valve_topic)
            if valve is None:
                self._log.error(f'valves._mqtt_result_handler: unknown topic: {valve_topic}')  # noqa: E501
                # TODO here is also possible to create new entries in valves
                # Table insted of creating them in class Boxes
                continue
            value = bool_to_int.get(payload[item], 0)
            if value == 1:
                await self._set_on_confirm(valve)
            else:
                await self._set_off_confirm(valve)
        return True

    async def _send_status_with_websocket(self, valve: Row, key: str) -> json:
        # TODO check if "key" is in valve:Row
        # is sqlite3.row a dict???
        ret = {
            'action': "status",
            'model': "valves",
            'id': valve['id'],
            'key': key,
            'value': valve[key],
        }
        ret = json.dumps(ret)
        await self._websockets.send_to_all(ret)
        return ret

    async def _send_mqtt(self, valve: Row, payload: str) -> bool:
        if self._mqtt.client is None:
            return False
        if not self._mqtt.client.is_connected:
            return False
        topic = "{prefix}/{topic}".format(
            prefix=self._options.mqtt_cmnd_prefix,
            topic=valve['topic'])
        self._mqtt.client.publish(topic, payload)
        return True

    async def _set_on_try(self, valve: Row) -> Row:
        with self._db_conn:
            self._db_conn.execute(
                'UPDATE valves SET is_running = ? WHERE id = ?',
                (-1, valve['id']))
        valve = await self.fetch_one_by_id(valve['id'])
        await self._send_status_with_websocket(valve, 'is_running')
        await self._send_mqtt(valve, 1)
        return valve

    async def _set_off_try(self, valve: Row) -> Row:
        with self._db_conn:
            self._db_conn.execute(
                'UPDATE valves SET is_running = ? WHERE id = ?',
                (-1, valve['id']))
        valve = await self.fetch_one_by_id(valve['id'])
        await self._send_status_with_websocket(valve, 'is_running')
        await self._send_mqtt(valve, 0)
        return valve

    async def _set_on_confirm(self, valve: Row) -> Row:
        last_run = datetime.now().strftime(self._options.time_format)
        with self._db_conn:
            self._db_conn.execute(
                'UPDATE valves SET is_running = ?, last_run = ?  WHERE id = ?',
                (1, last_run, valve['id']))

        valve = await self.fetch_one_by_id(valve['id'])
        await self._send_status_with_websocket(valve, 'is_running')
        await self._send_status_with_websocket(valve, 'last_run')
        tmp = valve['name']
        self._event_log.info(f'{tmp}: OFF')
        return valve

    async def _set_off_confirm(self, valve: Row) -> Row:
        with self._db_conn:
            self._db_conn.execute(
                'UPDATE valves SET is_running = ?  WHERE id = ?',
                (0, valve['id']))
        valve = await self.fetch_one_by_id(valve['id'])
        await self._send_status_with_websocket(valve, 'is_running')
        tmp = valve['name']
        self._event_log.info(f'{tmp}: OFF')
        return valve

    async def insert(self, item: dict) -> bool:
        try:
            with self._db_conn:
                cursor = self._db_conn.execute(
                    '''INSERT INTO valves
                    (name, box_id, topic)
                    VALUES (?, ?, ?)''',
                    (item['name'], item['box_id'], item['topic']))
        except IntegrityError:
            ret = None
        else:
            ret = cursor.lastrowid
        return ret

    async def update(self, item_id: int, item: dict) -> bool:
        ret = True
        try:
            with self._db_conn:
                self._db_conn.execute(
                    '''UPDATE valves
                    SET name = ?, remark = ?, duration = ?,
                    interval = ?, is_enabled = ?, hide = ?
                    WHERE id = ?''',
                    (item['name'], item['remark'],
                     item['duration'], item['interval'],
                     item['is_enabled'], item['hide'],
                     item_id))
        except IntegrityError:
            ret = False
        return ret

    async def delete(self, item_id: int) -> None:
        try:
            with self._db_conn:
                self._db_conn.execute(
                    'DELETE FROM valves WHERE id = ?',
                    (item_id,))
        except IntegrityError:
            # if nothing is deleted we don't get information,
            # lastrowid is in every case 0,
            # Exception is not raised
            pass
        return None

    async def fetch_one_by_key(self, key: str, value: Any) -> Row:
        c = self._db_conn.cursor()
        sql = f'''SELECT valves.*,
                boxes.topic AS box_topic, boxes.name AS box_name
                  FROM valves, boxes
                  WHERE valves.{key}= ? AND valves.box_id = boxes.id'''
        c.execute(sql, (value,))
        ret = c.fetchone()
        self._db_conn.commit()
        return ret

    async def fetch_one_by_id(self, item_id: int) -> Row:
        c = self._db_conn.cursor()
        c.execute('''SELECT valves.*,
                 boxes.topic AS box_topic, boxes.name AS box_name
                  FROM valves, boxes
                  WHERE valves.id= ? AND valves.box_id = boxes.id''',
                  (item_id,))
        ret = c.fetchone()
        self._db_conn.commit()
        return ret

    async def fetch_all(self) -> Row:
        c = self._db_conn.cursor()
        c.execute('''SELECT valves.*, 
                boxes.topic AS box_topic, boxes.name AS box_name
                  FROM valves, boxes
                  WHERE valves.box_id = boxes.id
                  ORDER BY valves.id''')
        ret = c.fetchall()
        self._db_conn.commit()
        return ret
