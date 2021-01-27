from datetime import datetime
import re
import json
from sqlite3 import IntegrityError, Row
from typing import Any, Dict


class Boxes():
    def __init__(self, app):
        self._db_conn = app['db'].conn
        self._mqtt = app['mqtt']
        self._log = app['log']
        self._options = app['options']
        self._mqtt.subscribe('tele/+/LWT', self._mqtt_lwt_handler)
        self._mqtt.subscribe('tele/+/STATE', self._mqtt_state_handler)
        self._mqtt.subscribe('tele/+/INFO1', self._mqtt_info_handler)
        self._mqtt.subscribe('tele/+/INFO2', self._mqtt_info_handler)

    async def _mqtt_lwt_handler(self, topic: str, payload: str) -> bool:
        self._log.debug(f'LWT: {topic}, payload: {payload}')
        box_topic = re.search('/(.*?)/', topic).group(1)
        first_seen = datetime.now().strftime(self._options.time_format)
        if payload == "Online":
            online_since = first_seen
        else:
            online_since = None
        try:
            with self._db_conn:
                self._db_conn.execute(
                    ''' INSERT INTO boxes
                    (topic, first_seen, online_since)
                    VALUES (?, ?, ?) ''',
                    (box_topic, first_seen, online_since))
        except IntegrityError:
            with self._db_conn:
                self._db_conn.execute(
                    'UPDATE boxes SET online_since = ?  WHERE topic = ?',
                    (online_since, box_topic))
        return True

    async def _mqtt_state_handler(self, topic: str, payload: str) -> bool:
        self._log.debug(f'State: {topic}, payload: {payload}')
        return True

    async def _mqtt_info_handler(self, topic: str, payload: str) -> bool:
        self._log.debug(f'Info: {topic}, payload: {payload}')
        return True

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

    async def fetch_all_json(self) -> str:
        c = self._db_conn.cursor()
        c.execute('SELECT * FROM boxes')
        ret = c.fetchall()
        self._db_conn.commit()
        ret = json.loads(ret)
        return ret
