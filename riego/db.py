import sqlite3
from pathlib import Path
from yoyo import read_migrations
from yoyo import get_backend

from logging import getLogger
_log = getLogger(__name__)

_instance = None


def get_db():
    global _instance
    return _instance


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
        self._options = options
        self.conn = None
        Path(self._options.db_filename).parent.mkdir(
            parents=True, exist_ok=True)

        self._do_migrations()

        try:
            self.conn = sqlite3.connect(self._options.db_filename,
                                        detect_types=sqlite3.PARSE_DECLTYPES)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            _log.error(f'Not able to connect to database: {e}')
            if self.conn is not None:
                self.conn.close()
            exit(1)

    def _do_migrations(self):
        try:
            backend = get_backend('sqlite:///' + self._options.db_filename)
        except Exception as e:
            _log.error(f'Not able to open database: {e}')
            exit(1)

        migrations = read_migrations(self._options.db_migrations_dir)
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))

    def __del__(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception as e:
            _log.error(f'database.py: not able to close conn: {e}')
