from datetime import datetime
import re
import json
import sys
from sqlalchemy.exc import IntegrityError

from riego.model.boxes import Box
from riego.model.valves import Valve


class Boxes():
    def __init__(self, app):
        self._db = app['db']
        self._mqtt = app['mqtt']
        self._log = app['log']
        self._options = app['options']
        self._mqtt.subscribe(self._options.mqtt_lwt_subscription,
                             self._mqtt_lwt_handler)
        self._mqtt.subscribe(self._options.mqtt_state_subscription,
                             self._mqtt_state_handler)
        self._mqtt.subscribe(self._options.mqtt_info1_subscription,
                             self._mqtt_info1_handler)
        self._mqtt.subscribe(self._options.mqtt_info2_subscription,
                             self._mqtt_info2_handler)

    async def _mqtt_lwt_handler(self, topic: str, payload: str) -> bool:
        """Create a new box or update an existing box

        :param topic: topic of mqtt message, "tele/+/LWT"
        :type topic: str
        :param payload: [description]
        :type payload: str
        :return: [description]
        :rtype: bool
        """
        self._log.debug(f'LWT: {topic}, payload: {payload}')
        box_topic = re.search('/(.*?)/', topic).group(1)
        session = self._db.Session()
        box = session.query(Box).filter(
            Box.topic == box_topic).first()
        if box is None:
            box = Box(topic=box_topic, name=box_topic)
            session.add(box)
        if payload == "Online":
            box.online_since = datetime.now()
        else:
            box.online_since = None
            # TODO set all "Valves" to "offline"
        session.commit()
        session.close()
        return True

    async def _mqtt_state_handler(self, topic: str, payload: str) -> bool:
        """Insert lines into valves table for every Channel found in 
        "/tele/+/STATE" message

        :param topic: topic from mqtt message, "/tele/+/STATE"
        :type topic: str
        :param payload: payload sfrom mqtt message
        :type payload: str
        :return: True on success
        :rtype: bool
        """
        self._log.debug(f'State: {topic}, payload: {payload}')

        box_topic = re.search('/(.*?)/', topic)
        if box_topic is None:
            return False
        box_topic = box_topic.group(1)

        session = self._db.Session()
        box = session.query(Box).filter(
            Box.topic == box_topic).first()
        if box is None:
            # normally not possible
            box = Box(topic=box_topic, name=box_topic)
            session.add(box)
            # Only neccessary if we have orphaned valves an next commit later
            # will fail
            session.commit()
        payload = json.loads(payload)

        for item in payload:
            # TODO if item "Wifi" take the Wifi nested dict and,
            #  search and extract "signal"
            channel_nr = re.match('^POWER(\d+)', item)  # noqa: W605
            if channel_nr is not None:
                channel_nr = channel_nr.group(1)
                valve = Valve(channel_nr=channel_nr,
                              name=f'{box_topic}, Channel {channel_nr}')
                box.valves.append(valve)
        try:
            session.commit()
        except IntegrityError:
            if self._options.verbose:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self._log.debug(f'Exception: {exc_type}')
            session.rollback()
        session.close()
        return True

    async def _mqtt_info1_handler(self, topic: str, payload: str) -> bool:
        """Update existing box with additional info

        :param topic: topic from mqtt message, "/tele/+/INFO1"
        :type topic: str
        :param payload: payload from mqtt mesage
        :type payload: str
        :return: [description]
        :rtype: bool
        """
        self._log.debug(f'Info: {topic}, payload: {payload}')
        box_topic = re.search('/(.*?)/', topic).group(1)

        payload = json.loads(payload)
        # TODO hw_type splitten in hw_type und hw_version
        hw_type = payload.get('Module', '')
        hw_version = ''
        # TODO sw_version splitten in sw_type und sw_version
        sw_version = payload.get('Version', '')
        sw_type = ''
        fallback_topic = payload.get('FallbackTopic', '')
        group_topic = payload.get('GroupTopic', '')

        session = self._db.Session()
        box = session.query(Box).filter(
            Box.topic == box_topic).first()
        if box is None:
            # normally not possible
            box = Box(topic=box_topic, name=box_topic)
            session.add(box)
        box.hw_type = hw_type
        box.hw_version = hw_version
        box.sw_type = sw_type
        box.sw_version = sw_version
        box.fallback_topic = fallback_topic
        box.group_topic = group_topic
        session.commit()
        session.close()
        return True

    async def _mqtt_info2_handler(self, topic: str, payload: str) -> bool:
        """Update existing box with additional info

        :param topic: topic from mqtt message, "/tele/+/INFO2"
        :type topic: str
        :param payload: payload from mqtt message
        :type payload: str
        :return: [description]
        :rtype: bool
        """
        self._log.debug(f'Info: {topic}, payload: {payload}')
        box_topic = re.search('/(.*?)/', topic).group(1)

        payload = json.loads(payload)
        hostname = payload.get('Hostname', '')
        ip_address = payload.get('IPAddress', '')

        session = self._db.Session()
        box = session.query(Box).filter(
            Box.topic == box_topic).first()
        if box is None:
            # normally not possible
            box = Box(topic=box_topic, name=box_topic)
            session.add(box)
        box.hostname = hostname
        box.ip_address = ip_address
        session.commit()
        session.close()
        return True
