import datetime
from pathlib import Path
from yoyo import read_migrations
from yoyo import get_backend

from sqlalchemy import (
    create_engine, Table, MetaData, Column, UniqueConstraint,
    Integer, String, DateTime, Boolean
)

import logging

meta = MetaData()

event_log = Table(
    'event_log', meta,
    Column('id', Integer, primary_key=True),
    Column('message', String),
    Column('level', String),
    Column('demo_int', Integer),
    Column('demo_str', String),
    Column('created_at', DateTime, default=datetime.datetime.now),
    Column('disabled', Boolean, default=1),
    UniqueConstraint('demo_int', 'demo_str', name='uix_1'),
)


class Database:
    def __init__(self, app):
        options = app['options']
        self.log = app['log']
        self.conn = None
        # create database path if not exist
        Path(options.database).parent.mkdir(parents=True, exist_ok=True)

        engine = create_engine('sqlite:///' +
                               options.database, echo=True)
        meta = MetaData()

        try:
            meta.create_all(engine)
        except Exception as e:
            print(e)

    def _run_yoyo_migrations(self):
        try:
            backend = get_backend('sqlite:///' + options.database)
        except Exception as e:
            self.log.critical(f'Not able to open database: {e}')
            exit(1)

        migrations = read_migrations(options.database_migrations_dir)

        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))

    def __del__(self):
        return None


class Options():
    def __init__(self):
        self.database = 'db/riego.db'


if __name__ == "__main__":
    app = {}
    options = Options()
    app['options'] = options
    logger = logging
    logging.basicConfig(level=logging.DEBUG)
    app['log'] = logger

    db = Database(app)
