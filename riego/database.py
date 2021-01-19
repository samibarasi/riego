import sqlite3
from pathlib import Path
from yoyo import read_migrations
from yoyo import get_backend


class Database:
    def __init__(self, app):
        options = app['options']
        log = app['log']
        self.conn = None
        Path(options.database).parent.mkdir(parents=True, exist_ok=True)
        backend = get_backend('sqlite:///' + options.database)
        migrations = read_migrations(options.database_migrations_dir)
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))
        try:
            self.conn = sqlite3.connect(options.database,
                                        detect_types=sqlite3.PARSE_DECLTYPES |
                                        sqlite3.PARSE_COLNAMES)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as error:
            log.info("sqlite3.connect error: " + str(error))
            if (self.conn):
                self.conn.close()

    def __del__(self):
        try:
            self.conn.close()
        except:
            print('Error')