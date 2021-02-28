from datetime import datetime
import re
import json

from sqlite3 import IntegrityError

from logging import getLogger
_log = getLogger(__name__)


bool_to_int = {'true': 1, 'false': 0, True: 1, False: 0,
               'True': 1, 'False': 0, 'on': 1, 'off': 0,
               'On': 1, 'Off': 0, 'ON': 1, 'OFF': 0}

int_to_js_bool = {1: "true", 0: "false", -1: "-1"}


_instance = None


def get_valves():
    global _instance
    return _instance


def setup_valves(options=None, db=None, mqtt=None, websockets=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Valves(options=options, db=db,
                       mqtt=mqtt, websockets=websockets)
    return _instance


class Valves():
    def __init__(self, options=None, db=None, mqtt=None, websockets=None):
        self._db_conn = db.conn
        self._mqtt = mqtt
        self._options = options
        self._websockets = websockets

        self.__is_running = None

        self._websockets.subscribe('valves', self._ws_handler)
        self._mqtt.subscribe(self._options.mqtt_result_subscription,
                             self._mqtt_result_handler)

    async def _ws_handler(self, msg: dict) -> None:
        _log.debug(f'In Valves._ws_handler: {msg}')
        if msg['action'] == 'update':
            await self.update_by_key(valve_id=msg['id'],
                                     key=msg['key'],
                                     value=msg['value'])
        return None

    async def _mqtt_result_handler(self, topic: str, payload: str) -> bool:
        """Dispatch mqtt messages:
        "stat/<box_topic>/RESULT {POWER1 :  ON}" (Is send after every cmnd)
        and store the state of channels to Database

        :param topic: Topic of subscribed MQTT-message
        :type topic: str
        :param payload: Payload of subscribed MQTT-message
        :type payload: str
        :return: [description]
        :rtype: bool
        """
        _log.debug(f'RESULT: {topic}, payload: {payload}')
        box_topic = re.search('/(.*?)/', topic)
        if box_topic is None:
            return False
        box_topic = box_topic.group(1)
        # convert payload to dict
        payload = json.loads(payload)
        # only one element in dict: {POWER1: ON}
        # extract channel_nr and status
        for key in payload:
            channel_nr = re.match('^POWER(\d+)', key)  # noqa: W605
            if channel_nr is None:
                return False
            channel_nr = channel_nr.group(1)
            status = payload[key]

            status = bool_to_int.get(status)
            if status == 1:
                await self._set_on_confirm(box_topic=box_topic,
                                           channel_nr=channel_nr)
            else:
                await self._set_off_confirm(box_topic=box_topic,
                                            channel_nr=channel_nr)
        return True

    async def _send_status_ws(self, valve_id=None, key=None, value=None):
        ret = {
            'action': "status",
            'scope': "valves",
            'id': valve_id,
            'key': key,
            'value': value,
        }
        ret = json.dumps(ret)
        await self._websockets.send_to_all(ret)
        return None

    async def _send_mqtt(self,
                         box_topic=None,
                         channel_nr=None,
                         payload=None) -> bool:
        if self._mqtt.client is None:
            return False
        if not self._mqtt.client.is_connected:
            return False

        topic = "{prefix}/{box_topic}/POWER{channel_nr}".format(
            prefix=self._options.mqtt_cmnd_prefix,
            box_topic=box_topic,
            channel_nr=channel_nr)
        self._mqtt.client.publish(topic, payload)
        return True

    async def set_on_try(self, valve_id) -> None:
        cursor = self._db_conn.cursor()
        cursor.execute('''UPDATE valves SET is_running = ?
                        WHERE id = ?''',(-1, valve_id))
        self._db_conn.commit()
        if cursor.rowcount < 1:
            _log.error("Unable to update")
            return None
        cursor.execute("""SELECT valves.*, boxes.topic AS box_topic
                    FROM valves, boxes
                    WHERE valves.box_id = boxes.id AND valves.id=?""",
                  (valve_id,))
        valve = cursor.fetchone()
        if valve is None:
            _log.error("Valve not found 001")
            return None
        await self._send_status_ws(valve_id=valve_id,
                                   key='is_running',
                                   value=-1)
        await self._send_mqtt(box_topic=valve['box_topic'],
                              channel_nr=valve['channel_nr'],
                              payload=self._options.mqtt_keyword_ON)
        return None

    async def set_off_try(self, valve_id) -> None:
        cursor = self._db_conn.cursor()
        cursor.execute('''UPDATE valves SET 
                        is_running = ?
                        WHERE id = ?''', (-1, valve_id))
        self._db_conn.commit()
        if cursor.rowcount < 1:
            _log.error("Unable to update:")
            return None
        cursor.execute("""SELECT valves.*, boxes.topic AS box_topic
                    FROM valves, boxes
                    WHERE valves.box_id = boxes.id AND valves.id=?""",
                  (valve_id,))
        valve = cursor.fetchone()
        if valve is None:
            _log.error("Valve not found 001a")
            return None
        await self._send_status_ws(valve_id=valve_id,
                                   key='is_running',
                                   value=-1)
        await self._send_mqtt(box_topic=valve['box_topic'],
                              channel_nr=valve['channel_nr'],
                              payload=self._options.mqtt_keyword_OFF)
        return None

    async def _set_on_confirm(self, box_topic=None, channel_nr=None) -> None:
        cursor = self._db_conn.cursor()
        cursor.execute("""SELECT valves.*, boxes.topic AS box_topic
                    FROM valves, boxes
                    WHERE valves.box_id = boxes.id
                    AND boxes.topic =?
                    AND valves.channel_nr=?""", (box_topic, channel_nr))
        valve = cursor.fetchone()
        if valve is None:
            _log.error("Valve not found 002")
            return None
        cursor.execute("""UPDATE valves SET
                        is_running = ?,
                        last_run = ?
                        WHERE id = ?""", (1, datetime.now(), valve['id']))
        self._db_conn.commit()
        if cursor.rowcount < 1:
            _log.error('Unable to update:')
            return None
        try:
            with self._db_conn:
                self._db_conn.execute(
                    "INSERT INTO events (valve_id) VALUES (?)",
                    (valve['id'],))
        except IntegrityError as e:
            _log.error(f'Unable to insert: {e}')

        await self._send_status_ws(valve_id=valve['id'],
                                   key='is_running',
                                   value=1)
        _log.info('Valve switched to ON: {}'.format(valve['name']))
        return None

    async def _set_off_confirm(self, box_topic=None, channel_nr=None) -> None:
        cursor = self._db_conn.cursor()
        cursor.execute("""SELECT valves.*, boxes.topic AS box_topic
                    FROM valves, boxes
                    WHERE valves.box_id = boxes.id
                    AND boxes.topic = ?
                    AND valves.channel_nr = ?""", (box_topic, channel_nr))
        valve = cursor.fetchone()
        if valve is None:
            _log.error("Valve not found 003")
            return None
        cursor.execute('''UPDATE valves SET 
                        is_running = ?
                        WHERE id = ?''', (0, valve['id']))
        self._db_conn.commit()
        if cursor.rowcount < 1:
            _log.error("Unable to update:")
            return None
        cursor.execute("""SELECT * FROM events
                    WHERE events.duration = 0
                    AND valve_id = ?
                    ORDER BY events.created_at DESC""", (valve['id'],))
        event = cursor.fetchone()
        if event is None:
            # Will happen after restart of Box
            _log.info("Event not found")
            return None
        # TODO sqlite should convert to datetime object
        duration = datetime.now() - event['created_at']
        duration = duration.total_seconds() / 60.0
        duration = round(duration)
        if duration == 0:
            duration = 1
        cursor.execute('''UPDATE events
                        SET duration = ?
                        WHERE id = ?''', (duration, event['id']))
        self._db_conn.commit()
        if cursor.rowcount < 1:
            _log.error("Unable to update")
            return None

        await self._send_status_ws(valve_id=valve['id'], key='is_running',
                                   value=0)
        _log.info('Valve switched to OFF: {}'.format(valve['name']))
        return None

    async def update_by_key(self, valve_id=None, key=None, value=None) -> bool:
        ret = True
        if key == "is_running":
            if bool_to_int.get(value, 0):
                await self.set_on_try(valve_id)
            else:
                await self.set_off_try(valve_id)
            return True
        # TODO sql-escape {key}
        sql = f"UPDATE valves SET {key} = ? WHERE id = ?"
        cursor = self._db_conn.cursor()
        cursor.execute(sql, (value, valve_id))
        self._db_conn.commit()
        if cursor.rowcount < 1:
            _log.error(f'Unable to update: {e}')
            ret = False
        print(f'valve_id={valve_id}, key={key}, value={value}')
        await self._send_status_ws(valve_id=valve_id, key=key, value=value)
        return ret


"""
   async def get_next(self, valve: Row) -> Row:
        valves = await self.fetch_all()
        count_valves = len(valves)
        if count_valves == 0:
            return None
        if valve is None:
            return valves[0]
        if count_valves == 1:
            return valves[0]
        for i in range(count_valves):
            if i == count_valves-1:
                return valves[0]
            if valve['id'] == valves[i]['id']:
                return valves[i+1]
        return None
"""
