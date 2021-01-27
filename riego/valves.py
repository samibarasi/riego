from datetime import datetime
import re
import json
from sqlite3 import IntegrityError, Row
from typing import Any


import riego.web.websockets

bool_to_int = {'true': 1, 'false': 0, True: 1, False: 0,
               'True': 1, 'False': 0, 'on': 1, 'off': 0,
               'On': 1, 'Off': 0, 'ON': 1, 'OFF': 0}

int_to_js_bool = {1: "true", 0: "false", -1: "-1"}


class Valves():
    def __init__(self, app):
        self._db_conn = app['db'].conn
        self._mqtt = app['mqtt']
        self._log = app['log']
        self._event_log = app['event_log']
        self._options = app['options']

        self.__is_running = None

        # TODO Dependency Injection for websockets
        riego.web.websockets.subscribe('valves', self._ws_handler)

        self._mqtt.subscribe(self._options.mqtt_result_subscription,
                             self._mqtt_result_handler)

    async def _ws_handler(self, msg: dict):
        """Find object from class valve with id=msg[id] and
        Call setter-method of Class Valve according to msg['prop']
        """
        self.log.debug(f'In Valves._ws_handler: {msg}')

        if not msg['action'] == 'update':
            return None
        valve = self.get_valve_by_id(msg['id'])
        func = getattr(valve, "set_" + msg['prop'])
        await func(msg['value'])

    async def _mqtt_result_handler(self, topic: str, payload: str) -> bool:
        """Dispatch mqtt message "stat/box_name/RESULT {POWER1 :  ON}"

        :param topic: Topic of subscribed MQTT-message
        :type topic: str
        :param payload: Payload of subscribed MQTT-message
        :type payload: str
        :return: [description]
        :rtype: bool
        """
        box = re.search('/(.*?)/', topic).group(1)
        payload = json.loads(payload)
        for channel in payload:
            topic = box + '/' + channel
            valve = self.get_valve_by_topic(topic)
            if valve is None:
                self.log.error(f'valves._mqtt_result_handler: unknown topic: {topic}')  # noqa: E501
                continue
            value = bool_to_int[payload[channel]]
            if value == 1:
                await valve._set_on_confirm()
            else:
                await valve._set_off_confirm()
        return True

    async def _send_status_with_websocket(self, valve: Row, key: str) -> json:
        ret = {
            'action': "status",
            'model': "valves",
            'id': valve['id'],
            'prop': key,
            'value': valve[key],
        }
        ret = json.dumps(ret)
        await riego.web.websockets.send_to_all(ret)
        return ret

    async def _send_mqtt(self, valve: Row, payload: str) -> bool:
        topic = "{prefix}/{box_topic}/{channel}".format(
            prefix=self._options.mqtt_cmnd_prefix,
            box_topic=valve['box_topic'],
            channel=valve['channel'])
        if self._mqtt.client is None:
            return False
        if not self._mqtt.client.is_connected:
            return False
            self._mqtt.client.publish(topic, 1)
        return False

    async def _set_on_try(self, valve: Row) -> Row:
        with self._db_conn:
            self._db_conn.execute(
                'UPDATE valves SET is_running = ? WHERE id = ?',
                (-1, valve['id']))
        valve = self.fetch_one_by_id(valve['id'])
        await self._send_status_with_websocket(valve, 'is_running')
        await self._send_mqtt(valve, 1)
        return valve

    async def _set_off_try(self, valve: Row) -> Row:
        with self._db_conn:
            self._db_conn.execute(
                'UPDATE valves SET is_running = ? WHERE id = ?',
                (-1, valve['id']))
        valve = self.fetch_one_by_id(valve['id'])
        await self._send_status_with_websocket(valve, 'is_running')
        await self._send_mqtt(valve, 0)
        return valve

    async def _set_on_confirm(self, valve: Row) -> Row:
        last_run = datetime.now().strftime(self._options.time_format)
        with self._db_conn:
            self._db_conn.execute(
                'UPDATE valves SET is_running = ?, last_run = ?  WHERE id = ?',
                (1, last_run, valve['id']))

        valve = self.fetch_one_by_id(valve['id'])
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
        valve = self.fetch_one_by_id(valve['id'])
        await self._send_status_with_websocket(valve, 'is_running')
        tmp = valve['name']
        self._event_log.info(f'{tmp}: OFF')
        return valve

    async def insert(self, item: dict) -> bool:
        try:
            with self._db_conn:
                cursor = self._db_conn.execute(
                    '''INSERT INTO valves
                    (name, box_id, channel)
                    VALUES (?, ?, ?)''',
                    (item['name'], item['box_id'], item['channel']))
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
        sql = f'''SELECT valves.*, boxes.topic AS box_topic
                  FROM valves, boxes
                  WHERE valves.{key}= ? AND valves.box_id = boxes.id'''
        c.execute(sql, (value,))
        ret = c.fetchone()
        self._db_conn.commit()
        return ret

    async def fetch_one_by_id(self, item_id: int) -> Row:
        c = self._db_conn.cursor()

        c.execute('''SELECT valves.*, boxes.topic AS box_topic
                  FROM valves, boxes
                  WHERE valves.id= ? AND valves.box_id = boxes.id''',
                  (item_id,))
        ret = c.fetchone()
        self._db_conn.commit()
        return ret

    async def fetch_all(self) -> Row:
        c = self._db_conn.cursor()
        c.execute('''SELECT valves.*, boxes.topic AS box_topic
                  FROM valves, boxes
                  WHERE valves.box_id = boxes.id''')
        ret = c.fetchall()
        self._db_conn.commit()
        return ret

    async def fetch_all_json(self) -> str:
        c = self._db_conn.cursor()
        c.execute('''SELECT valves.*, boxes.topic AS box_topic
                  FROM valves, boxes
                  WHERE valves.box_id = boxes.id''')
        ret = c.fetchall()
        self._db_conn.commit()
        return json.loads(ret)
