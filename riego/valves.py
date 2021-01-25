from datetime import datetime
import json
import riego.web.websockets
import re

bool_to_int = {'true': 1, 'false': 0, True: 1, False: 0,
               'True': 1, 'False': 0, 'on': 1, 'off': 0,
               'On': 1, 'Off': 0, 'ON': 1, 'OFF': 0}

int_to_js_bool = {1: "true", 0: "false", -1: "-1"}


class Valve():
    def __init__(self, row, app):
        self.__db_conn = app['db'].conn
        self.__mqtt = app['mqtt']
        self.__event_log = app['event_log']
        self.__options = app['options']

        self.__id = row['id']
        self.__name = row['name']
        self.__remark = row['remark']

        self.__channel = row['channel']
        self.__topic = row['box_topic'] + "/" + row['channel']
        self.__duration = row['duration']
        self.__interval = row['interval']
        self.__last_run = row['last_run']
        self.__is_running = row['is_running']
        self.__is_enabled = row['is_enabled']

        self.__box_display_name = row['box_display_name']
        self.__box_id = row['box_id']

    @ property
    def id(self):
        return self.__id

    @ property
    def name(self):
        return self.__name

    async def set_name(self, val: str):
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET name = ?  WHERE id = ?',
                (val, self.__id))
        await self.send_status_with_websocket('name', val)
        self.__name = val

    @ property
    def topic(self):
        return self.__topic

    async def set_topic(self, val) -> NotImplementedError:
        raise NotImplementedError

    @ property
    def duration(self):
        return self.__duration

    async def set_duration(self, val: int):
        val = int(val)
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET duration = ?  WHERE id = ?',
                (val, self.__id))
        await self.send_status_with_websocket('duration', val)
        self.__duration = val

    @ property
    def interval(self):
        return self.__interval

    async def set_interval(self, val: int):
        val = int(val)
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET interval = ?  WHERE id = ?',
                (val, self.__id))
        await self.send_status_with_websocket('interval', val)
        self.__interval = val

    @ property
    def last_run(self) -> datetime:
        """Convert to datetime object before return

        :return: Last ON-Time of valve
        :rtype: datetime
        """
        return datetime.strptime(self.__last_run, self.__options.time_format)

    async def set_last_run(self):
        raise NotImplementedError

    @ property
    def is_running(self):
        return self.__is_running

    async def set_is_running(self, val):
        val = bool_to_int[val]
        if val:
            await self._set_on_try()
        else:
            await self._set_off_try()

    @ property
    def is_enabled(self):
        return self.__is_enabled

    async def set_is_enabled(self, val):
        val = bool_to_int[val]

        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET is_enabled = ?  WHERE id = ?',
                (val, self.__id))
        await self.send_status_with_websocket('is_enabled', val)
        self.__is_enabled = val

    @ property
    def remark(self):
        return self.__remark

    async def set_remark(self, val):
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET remark = ?  WHERE id = ?',
                (val, self.__id))
        await self.send_status_with_websocket('remark', val)
        self.__remark = val

    def get_dict(self):
        ret = {'id': self.__id,
               'name': self.__name,
               'topic': self.__topic,
               'duration': self.__duration,
               'interval': self.__interval,
               'last_run': self.__last_run,
               'is_running': self.__is_running,
               'is_enabled': self.__is_enabled,
               'remark': self.__remark}
        return ret

    async def send_status_with_websocket(self, prop, value):
        ret = {
            'action': "status",
            'model': "valves",
            'id': self.__id,
            'prop': prop,
            'value': value,
        }
        ret = json.dumps(ret)
        await riego.web.websockets.send_to_all(ret)
        return ret

    async def _set_on_try(self) -> bool:
        self.__is_running = -1
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET is_running = ?  WHERE id = ?',
                (self.__is_running, self.__id))
        topic = self.__options.mqtt_cmnd_prefix + '/' + self.__topic
        await self.send_status_with_websocket('is_running', -1)
        if self.__mqtt.client is None:
            return False
        if not self.__mqtt.client.is_connected:
            return False
        self.__mqtt.client.publish(topic, 1)
        return True

    async def _set_off_try(self) -> bool:
        self.__is_running = -1
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET is_running = ?  WHERE id = ?',
                (self.__is_running, self.__id))
        await self.send_status_with_websocket('is_running', -1)
        if self.__mqtt.client is None:
            return False
        if not self.__mqtt.client.is_connected:
            return False
        topic = self.__options.mqtt_cmnd_prefix + '/' + self.__topic
        self.__mqtt.client.publish(topic, 0)
        return True

    async def _set_on_confirm(self):
        self.__is_running = 1
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET is_running = ?  WHERE id = ?',
                (self.__is_running, self.__id))
        await self.send_status_with_websocket('is_running', 1)

        self.__last_run = datetime.now().strftime(self.__options.time_format)
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET last_run = ?  WHERE id = ?',
                (self.__last_run, self.__id))
        await self.send_status_with_websocket('last_run', self.__last_run)

    async def _set_off_confirm(self):
        self.__is_running = 0
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET is_running = ?  WHERE id = ?',
                (self.__is_running, self.__id))
        await self.send_status_with_websocket('is_running', 0)


class Valves():
    def __init__(self, app):
        db_conn = app['db'].conn
        mqtt = app['mqtt']
        self.log = app['log']
        self.options = app['options']

        self._valves = []
        self.idx_valves = -1
        sql = '''SELECT valves.*, 
            boxes.id AS box_id,
            boxes.topic AS box_topic,
            boxes.display_name AS box_display_name
            FROM valves, boxes 
            WHERE valves.box_id = boxes.id;'''
        for row in db_conn.execute(sql):
            v = Valve(row, app)
            self._valves.append(v)
# TODO Dependenca Injection for websockets.
        riego.web.websockets.subscribe('valves', self._ws_handler)
        mqtt.subscribe(self.options.mqtt_result_subscription,
                       self._mqtt_result_handler)

    def get_next(self):
        self.idx_valves += 1
        if len(self._valves) == 0:
            return None
        if self.idx_valves >= len(self._valves):
            self.idx_valves = 0
        return self._valves[self.idx_valves]

    def get_dict_of_all(self) -> dict:
        """Create dict of properties and value from all
        objects of valves. used for updating HTML-page

        :return: dict with all properties of all valves
        :rtype: dict
        """
        ret = {}
        for v in self._valves:
            ret[v.id] = v.get_dict()
        return ret

    def get_valve_by_id(self, id: int) -> Valve:
        """Returns Valve-Object from database with given id.

        :param id: Unique id from database
        :type id: int
        :return: None if not found
        :rtype: Valve
        """
        for v in self._valves:
            if v.id == int(id):
                return v
        return None

    def get_valve_by_topic(self, topic: str) -> Valve:
        """Returns Valve-Object from database with given topic

        :param topic: Unique topic from database
        :type topic: str
        :return: None if not found
        :rtype: Valve
        """
        for v in self._valves:
            if v.topic == topic:
                return v
        return None

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
