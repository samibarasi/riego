import sqlite3
import json
import asyncio
import datetime
from pathlib import Path
from yoyo import read_migrations
from yoyo import get_backend

from riego.web.websockets import get_websockets

from logging import getLogger
_log = getLogger(__name__)

_instance = None


def get_db():
    global _instance
    return _instance


def transformValue(value):
    # transform date to string
    if isinstance(value, datetime.datetime):
        value = value.strftime("%d.%m.%y %H:%M:%S")
    return value

def query_db(query, args=(), one=False):
    cur = get_db().conn.cursor()
    cur.execute(query, args)
    r = [dict((cur.description[i][0], transformValue(value)) for i, value in enumerate(row)) for row in cur.fetchall()]
    # r = []
    # for row in cur.fetchall():
    #     for i, value in enumerate(row):
    #         r.append(dict((cur.description[i][0], transformValue(value))))
        
    return (r[0] if r else None) if one else r


def setup_db(options=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Db(options=options)
    return _instance


class Db:
    def __init__(self, options=None):
        global _instance
        if _instance is None:
            _instance = self

        self.conn = None
        Path(options.db_filename).parent.mkdir(
            parents=True, exist_ok=True)

        self._do_migrations(options)

        try:
            self.conn = sqlite3.connect(options.db_filename,
                                        detect_types=sqlite3.PARSE_DECLTYPES)
        except Exception as e:
            _log.error(f'Unable to connect to database: {e}')
            if self.conn is not None:
                self.conn.close()
            exit(1)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row

        self.conn.create_function("db_to_websocket", 2, self._db_to_websocket)
        self.conn.execute("DROP TRIGGER IF EXISTS t_valves_update")
        self.conn.execute("""CREATE TRIGGER t_valves_update
                AFTER UPDATE ON valves
                WHEN old.is_hidden <> new.is_hidden
                BEGIN SELECT db_to_websocket('valves', 'reload'); END""")

        self.conn.execute("DROP TRIGGER IF EXISTS t_events_insert")
        self.conn.execute("""CREATE TRIGGER t_events_insert
                AFTER INSERT ON events
                BEGIN SELECT db_to_websocket('events', 'reload'); END""")

        self.conn.execute("DROP TRIGGER IF EXISTS t_events_update")
        self.conn.execute("""CREATE TRIGGER t_events_update
                AFTER UPDATE ON events
                BEGIN SELECT db_to_websocket('events', 'reload'); END""")

        self.conn.execute("DROP TRIGGER IF EXISTS t_boxes_update")
        self.conn.execute("""CREATE TRIGGER t_boxes_update
                AFTER UPDATE ON boxes
                BEGIN SELECT db_to_websocket('boxes', 'reload'); END""")

    def _do_migrations(self, options):
        try:
            backend = get_backend('sqlite:///' + options.db_filename)
        except Exception as e:
            _log.error(f'Unable to open database: {e}')
            exit(1)

        migrations = read_migrations(options.db_migrations_dir)
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))

    def _db_to_websocket(self, scope: str, action: str):
        """Dispatch callback from database and send
        a message to client Browser with websocket

        :param scope: Name of functional part of Webpage
        :type scope: str
        :param action: Action that the Webpage should do
        :type action: str
        """
        message = {
            'action': action,
            'scope': scope,
        }
        message = json.dumps(message)
        ws = get_websockets()
        loop = asyncio.get_event_loop()
        loop.create_task(ws.send_to_all(message))

    def __del__(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception as e:
            _log.error(f'database.py: Unable to close Databse: {e}')
