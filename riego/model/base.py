from pathlib import Path
from yoyo import read_migrations
from yoyo import get_backend

from sqlalchemy import (
    create_engine
)
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class Database:
    def __init__(self, app):
        self._options = app['options']
        self._log = app['log']
        # create database path if not exist
        Path(self._options.database).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine('sqlite:///' +
                                    self._options.database, echo=False)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

        if not Path(self._options.database).is_file():
            self._create_with_sa()
        
        #    self._migrate_with_yoyo()

    def _create_with_sa(self) -> None:
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            self._log.critical(f'Not able to open database: {e}')
            exit(1)
        return None

    def _migrate_with_yoyo(self) -> None:
        try:
            backend = get_backend('sqlite:///' + self._options.database)
        except Exception as e:
            self._log.critical(f'Not able to open database: {e}')
            exit(1)
        migrations = read_migrations(self._options.database_migrations_dir)
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))
        return None

    def __del__(self):
        self.Session.remove()
        return None
