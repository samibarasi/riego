import sqlite3
from pathlib import Path
from yoyo import read_migrations
from yoyo import get_backend

_instance = None


def get_db():
    global _instance
    return _instance.conn


def setup_db(app):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Db(app)
    return _instance


class Db:
    def __init__(self, app):
        global _instance
        if _instance is None:
            _instance = self
        options = app['options']
        self.conn = None
        Path(options.db_filename).parent.mkdir(parents=True, exist_ok=True)
        try:
            backend = get_backend('sqlite:///' + options.db_filename)
        except Exception as e:
            self.log.error(f'Not able to open database: {e}')
            exit(1)

        migrations = read_migrations(options.db_migrations_dir)

        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))
        try:
            self.conn = sqlite3.connect(options.db_filename,
                                        detect_types=sqlite3.PARSE_DECLTYPES)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            self.log.error(f'Not able to connect to database: {e}')
            if self.conn is not None:
                self.conn.close()
            exit(1)

    def __del__(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception as e:
            self.log.error(f'database.py: not able to close conn: {e}')
