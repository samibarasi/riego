from datetime import datetime
import re
import json
from sqlite3 import IntegrityError, Row
from typing import Any

from logging import getLogger
_log = getLogger(__name__)

_instance = None


def get_boxes():
    global _instance
    return _instance


def setup_boxes(options=None, db=None, mqtt=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Boxes(options=options, db=db, mqtt=mqtt)
    return _instance


class Boxes():
    def __init__(self, options=None, db=None, mqtt=None):
        global _instance
        if _instance is None:
            _instance = self

        self._db_conn = db.conn
        self._mqtt = mqtt
        self._options = options

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
        This message comes from Tasmota only on startup and if
        we send a message for delete this reatained message from mqtt broker

        :param topic: topic of mqtt message, "tele/+/LWT"
        :type topic: str
        :param payload: [description]
        :type payload: str
        :return: [description]
        :rtype: bool
        """
        _log.debug(f'LWT: {topic}, payload: {payload}')
        if payload is None or payload == '':
            # Could be a retain delete message
            return

        box_topic = re.search('/(.*?)/', topic)
        if box_topic is None:
            return False
        box_topic = box_topic.group(1)

        first_seen = datetime.now()
        if payload == "Online":
            online_since = first_seen
        if payload == "Offline":
            online_since = None
            # TODO set all "Valves" to "offline"

        try:
            with self._db_conn:
                self._db_conn.execute(
                    ''' INSERT INTO boxes
                    (name, topic, first_seen, online_since)
                    VALUES (?, ?, ?, ?) ''',
                    (box_topic, box_topic, first_seen, online_since))
        except IntegrityError:
            with self._db_conn:
                self._db_conn.execute(
                    'UPDATE boxes SET online_since = ?  WHERE topic = ?',
                    (online_since, box_topic))
        return True

    async def _mqtt_state_handler(self, topic: str, payload: str) -> bool:
        """Insert lines into valves table for every Channel found in
        "/tele/+/STATE" message

        This message comes from Tasmota on startup and in intervalls

        :param topic: topic from mqtt message, "/tele/+/STATE"
        :type topic: str
        :param payload: payload sfrom mqtt message
        :type payload: str
        :return: True on success
        :rtype: bool
        """
        _log.debug(f'State: {topic}, payload: {payload}')
        if payload is None or payload == '':
            # Could be a config message
            return False

        box_id, box_topic = await self._get_box_id_by_topic(topic=topic)

        payload = json.loads(payload)
        for item in payload:
            # TODO if item "Wifi" take the Wifi nested dict and,
            #  search and extract "signal"
            channel_nr = re.match('^POWER(\d+)', item)  # noqa: W605
            if channel_nr is not None:
                channel_nr = channel_nr.group(1)
                try:
                    with self._db_conn:
                        self._db_conn.execute(
                            """INSERT INTO valves (channel_nr, box_id, name)
                            VALUES (?,?,?)""",
                            (channel_nr, box_id,
                             f'{box_topic}, Power {channel_nr}')
                        )
                except IntegrityError:
                    # _log.debug(f'unable to Update MQTT STATE:{e}')
                    pass
        return True

    async def _mqtt_info1_handler(self, topic: str, payload: str) -> bool:
        """Update existing box with additional info
        This message comes from Tasmota only on startup

        :param topic: topic from mqtt message, "/tele/+/INFO1"
        :type topic: str
        :param payload: payload from mqtt mesage
        :type payload: str
        :return: [description]
        :rtype: bool
        """
        _log.debug(f'Info1: {topic}, payload: {payload}')
        if payload is None or payload == '':
            # Could be a config message
            return False

        box_id, box_topic = await self._get_box_id_by_topic(topic=topic)

        payload = json.loads(payload)
        # TODO hw_type splitten in hw_type und hw_version
        hw_type = payload.get('Module', '')
        hw_version = ''
        # TODO sw_version splitten in sw_type und sw_version
        sw_version = payload.get('Version', '')
        sw_type = ''
        fallback_topic = payload.get('FallbackTopic', '')
        group_topic = payload.get('GroupTopic', '')

        cursor = self._db_conn.cursor()
        cursor.execute("""UPDATE boxes
                    SET hw_type = ?, hw_version = ?,
                    sw_type= ?, sw_version = ?,
                    fallback_topic = ?, group_topic = ?
                    WHERE id = ?""",
                    (hw_type, hw_version, sw_type, sw_version,
                     fallback_topic, group_topic, box_id))
        self._db_conn.commit()
        if cursor.rowcount < 1:
            _log.debug(f'unable to Update MQTT INFO1:{e}')
            return False
        return True

    async def _mqtt_info2_handler(self, topic: str, payload: str) -> bool:
        """Update existing box with additional info
        This message comes from Tasmota only on startup

        :param topic: topic from mqtt message, "/tele/+/INFO2"
        :type topic: str
        :param payload: payload from mqtt message
        :type payload: str
        :return: [description]
        :rtype: bool
        """
        _log.debug(f'Info2: {topic}, payload: {payload}')
        if payload is None or payload == '':
            # Could be a config message
            return False

        box_id, box_topic = await self._get_box_id_by_topic(topic=topic)

        payload = json.loads(payload)
        hostname = payload.get('Hostname', '')
        ip_address = payload.get('IPAddress', '')

        cursor = self._db_conn.cursor()
        cursor.execute("""UPDATE boxes
                    SET hostname = ?, ip_address = ?
                    WHERE id = ?""",
                    (hostname, ip_address, box_id))
        self._db_conn.commit()
        if cursor.rowcount < 1:
            _log.debug(f'unable to Update MQTT INFO2:{e}')
            return False
        return True

    async def _get_box_id_by_topic(self, topic=None):
        box_topic = re.search('/(.*?)/', topic)
        if box_topic is None:
            return False
        box_topic = box_topic.group(1)

        cursor = self._db_conn.cursor()
        cursor.execute('SELECT * FROM boxes WHERE topic=?', (box_topic,))
        item = cursor.fetchone()
        self._db_conn.commit()
        if item is None:
            with self._db_conn:
                cursor = self._db_conn.execute(
                    ''' INSERT INTO boxes
                    (name, topic, first_seen, online_since)
                    VALUES (?, ?, ?, ?) ''',
                    (box_topic, box_topic, datetime.now(), datetime.now()))
            box_id = cursor.lastrowid
        else:
            box_id = item['id']
        return box_id, box_topic

# Section with unused functions
#
#

    async def insert(self, item: dict) -> bool:
        try:
            with self._db_conn:
                cursor = self._db_conn.execute(
                    ''' INSERT INTO boxes
                    (topic, display_name, remark)
                    VALUES (?, ?, ?) ''',
                    (item['topic'], item['display_name'], item['remark']))
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
                    ''' UPDATE boxes
                        SET display_name = ?, remark = ?
                        WHERE id = ? ''',
                    (item['display_name'], item['remark'], item_id))
        except IntegrityError:
            ret = False
        return ret

    async def delete(self, item_id: int) -> None:
        try:
            with self._db_conn:
                self._db_conn.execute(
                    'DELETE FROM boxes WHERE id = ?',
                    (item_id,))
        except IntegrityError:
            pass
        return None

    async def fetch_one_by_key(self, key: str, value: Any) -> Row:
        c = self._db_conn.cursor()
        sql = f'SELECT * FROM boxes WHERE {key}=?'
        c.execute(sql, (value,))
        ret = c.fetchone()
        self._db_conn.commit()
        return ret

    async def fetch_one_by_id(self, item_id: int) -> Row:
        c = self._db_conn.cursor()
        c.execute('SELECT * FROM boxes WHERE id=?', (item_id,))
        ret = c.fetchone()
        self._db_conn.commit()
        return ret

    async def fetch_all(self) -> Row:
        c = self._db_conn.cursor()
        c.execute('SELECT * FROM boxes')
        ret = c.fetchall()
        self._db_conn.commit()
        return ret
