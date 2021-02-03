from datetime import datetime

import re
import json
from riego.model.valves import Valve
from riego.model.events import Event
from riego.model.boxes import Box
from sqlalchemy.exc import IntegrityError


bool_to_int = {'true': 1, 'false': 0, True: 1, False: 0,
               'True': 1, 'False': 0, 'on': 1, 'off': 0,
               'On': 1, 'Off': 0, 'ON': 1, 'OFF': 0}

int_to_js_bool = {1: "true", 0: "false", -1: "-1"}


class Valves():
    def __init__(self, app):
        self._db = app['db']
        self._Valve = Valve()
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
            'model': "valves",
            'id': valve_id,
            'key': key,
            'value': value,
        }
        ret = json.dumps(ret)
        await self._websockets.send_to_all(ret)
        return None

    async def _send_document_reload_ws(self) -> None:
        ret = {
            'action': "reload",
            'model': "valves",
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
        session = self._db.Session()
        valve = session.query(Valve).get(valve_id)
        valve.is_running = -1
        await self._send_status_ws(valve_id=valve_id,
                                   key='is_running',
                                   value=-1)
        await self._send_mqtt(box_topic=valve.box.topic,
                              channel_nr=valve.channel_nr,
                              payload=self._options.mqtt_keyword_ON)
        session.commit()
        session.close()
        return None

    async def set_off_try(self, valve_id) -> None:
        session = self._db.Session()
        valve = session.query(Valve).get(valve_id)
        valve.is_running = -1
        await self._send_status_ws(valve_id=valve_id,
                                   key='is_running',
                                   value=-1)
        await self._send_mqtt(box_topic=valve.box.topic,
                              channel_nr=valve.channel_nr,
                              payload=self._options.mqtt_keyword_OFF)
        session.commit()
        session.close()
        return None

    async def _set_on_confirm(self, box_topic=None, channel_nr=None) -> None:
        session = self._db.Session()
        valve = session.query(Valve).filter(Box.topic == box_topic,
                                            Valve.channel_nr == channel_nr).first()  # noqa: E501
        if valve is None:
            session.close()
            return
        valve.is_running = 1
        self._log.info(f'Valve switched to ON: {valve.name}')
        await self._send_status_ws(valve_id=valve.id,
                                   key='is_running',
                                   value=valve.is_running)
        event = Event()
        valve.events.append(event)
        session.commit()
        session.close()
        return None

    async def _set_off_confirm(self,  box_topic=None, channel_nr=None) -> None:
        session = self._db.Session()
        valve = session.query(Valve).filter(Box.topic == box_topic,
                                            Valve.channel_nr == channel_nr).first()  # noqa: E501
        if valve is None:
            session.close()
            return
        valve.is_running = 0
        self._log.info(f'Valve switched to OFF: {valve.name}')
        await self._send_status_ws(valve_id=valve.id, key='is_running',
                                   value=valve.is_running)

        event = session.query(Event).filter(
            Event.valve_id == valve.id, Event.duration == 0).order_by(Event.created_at.desc()).first()  # noqa: E501

        duration = datetime.now() - event.created_at
        duration = duration.total_seconds() / 60.0
        event.duration = duration
        session.commit()
        session.close()
        return None

    async def update_by_key(self, valve_id=None, key=None, value=None) -> bool:
        ret = True
        if key == "is_running":
            if bool_to_int.get(value, 0):
                await self.set_on_try(valve_id)
            else:
                await self.set_off_try(valve_id)
            return True

        session = self._db.Session()
        valve = session.query(Valve).get(valve_id)
        setattr(valve, key, value)
        try:
            session.commit()
        except IntegrityError as e:
            self._log.error(f'valves.py: {e}')
            ret = False
        print(f'valve_id={valve_id}, key={key}, value={value}')
        await self._send_status_ws(valve_id=valve_id, key=key, value=value)
        session.close()
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
