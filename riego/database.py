import sqlite3
from pathlib import Path
from yoyo import read_migrations
from yoyo import get_backend


class Database:
    def __init__(self, app):
        options = app['options']
        self.log = app['log']
        self.conn = None
        Path(options.database).parent.mkdir(parents=True, exist_ok=True)
        try:
            backend = get_backend('sqlite:///' + options.database)
        except Exception as e:
            self.log.error(f'Not able to open database: {e}')
            exit(1)

        migrations = read_migrations(options.database_migrations_dir)

        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))
        try:
            self.conn = sqlite3.connect(options.database)
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
