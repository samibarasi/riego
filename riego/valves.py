from datetime import datetime
import json
import riego.web.websockets


class Valves():
    def __init__(self, app):
        db_conn = app['db'].conn
        mqtt = app['mqtt']
        event_log = app['event_log']
        self.log = app['log']
        self._valves = []
        self.idx_valves = -1
        for row in db_conn.execute('select * from valves'):
            v = Valve(db_conn, mqtt, event_log, row)
            self._valves.append(v)

        riego.web.websockets.subscribe('valves', self._ws_handler)

    def get_next(self):
        self.idx_valves += 1
        if len(self._valves) == 0:
            return None
        if self.idx_valves >= len(self._valves):
            self.idx_valves = 0
        return self._valves[self.idx_valves]

    def get_dict(self):
        ret = {}
        for v in self._valves:
            ret[v.id] = v.get_dict()
        return ret

    def get_valve_by_id(self, id: int):
        for v in self._valves:
            if v.id == int(id):
                return v
        return None

    async def _ws_handler(self, msg: dict):
        """
        Call function from Object Valves according to msg['propo']
        """
        if not msg['action'] == 'update':
            return None
        valve = self.get_valve_by_id(msg['id'])
        func = getattr(valve, "set_" + msg['prop'])
        await func(msg['value'])


class Valve():

    def __init__(self, db_conn, mqtt, event_log, row):
        self.__db_conn = db_conn
        self.__mqtt = mqtt
        self.__event_log = event_log

        self.bool_to_int = {'true': 1, 'false': 0, True: 1, False: 0,
                            'True': 1, 'False': 0, 'on': 1, 'off': 0,
                            'On': 1, 'Off': 0, 'ON': 1, 'OFF': 0}

        self.__id = row['id']
        self.__name = row['name']
        self.__topic = row['topic']
        self.__duration = row['duration']
        self.__interval = row['interval']
        self.__last_run = row['last_run']
        self.__is_running = row['is_running']
        self.__is_enabled = row['is_enabled']
        self.__remark = row['remark']

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

    async def set_topic(self, val: str):
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET topic = ?  WHERE id = ?',
                (val, self.__id))
        await self.send_status_with_websocket('topic', val)
        self.__topic = val

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
    def last_run(self):
        return self.__last_run

    def set_last_run(self):
        raise NotImplementedError

    @ property
    def is_running(self):
        return self.__is_running

    async def set_is_running(self, val):
        val = self.bool_to_int[val]
        with self.__db_conn:
            self.__db_conn.execute(
                'UPDATE valves SET is_running = ?  WHERE id = ?',
                (val, self.__id))
        self.__mqtt.client.publish(self.__topic, val)
        self.__event_log.info(str(val) + ';' + self.name)
        await self.send_status_with_websocket('is_running', val)
        if val == 1:
            self.__last_run = datetime.now()
            with self.__db_conn:
                self.__db_conn.execute(
                    'UPDATE valves SET last_run = ?  WHERE id = ?',
                    (self.__last_run, self.__id))
            await self.send_status_with_websocket('last_run',
                                                  str(self.__last_run))
        self.__is_running = val

    @ property
    def is_enabled(self):
        return self.__is_enabled

    async def set_is_enabled(self, val):
        val = self.bool_to_int[val]

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
               'last_run': str(self.__last_run),
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
