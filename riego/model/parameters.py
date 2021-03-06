from sqlite3 import IntegrityError

from logging import getLogger
_log = getLogger(__name__)

_instance = None


def get_parameters():
    global _instance
    return _instance


def setup_parameters(app=None, options=None, db=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Parameters(app=app, options=options, db=db)
    return _instance


class Parameters:
    def __init__(self, app=None, options=None, db=None):
        global _instance
        if _instance is None:
            _instance = self
        self._db_conn = db.conn

        self._start_time_1 = None
        self._max_duration = None
        self._smtp_hostname = None
        self._smtp_port = None
        self._smtp_security = None
        self._smtp_user = None
        self._smtp_password = None
        self._smtp_from = None

        self._cloud_identifier = None
        self._cloud_server_url = None

        self._ssh_server_hostname = None
        self._ssh_server_port = None
        self._ssh_server_listen_port = None
        self._ssh_user_key = None

        self._load_all()

    @property
    def start_time_1(self):
        return self._start_time_1

    @start_time_1.setter
    def start_time_1(self, value):
        self._start_time_1 = value
        self._update_value_by_key(key="start_time_1", value=value)

    @property
    def max_duration(self):
        return int(self._max_duration)

    @max_duration.setter
    def max_duration(self, value):
        self._max_duration = value
        self._update_value_by_key(key="max_duration", value=value)

    @property
    def smtp_hostname(self):
        return self._smtp_hostname

    @smtp_hostname.setter
    def smtp_hostname(self, value):
        self._smtp_hostname = value
        self._update_value_by_key(key="smtp_hostname", value=value)

    @property
    def smtp_port(self):
        return self._smtp_port

    @smtp_port.setter
    def smtp_port(self, value):
        self._smtp_port = value
        self._update_value_by_key(key="smtp_port", value=value)

    @property
    def smtp_security(self):
        return self._smtp_security

    @smtp_security.setter
    def smtp_security(self, value):
        self._smtp_security = value
        self._update_value_by_key(key="smtp_security", value=value)

    @property
    def smtp_user(self):
        return self._smtp_user

    @smtp_user.setter
    def smtp_user(self, value):
        self._smtp_user = value
        self._update_value_by_key(key="smtp_user", value=value)

    @property
    def smtp_password(self):
        return self._smtp_password

    @smtp_password.setter
    def smtp_password(self, value):
        self._smtp_password = value
        self._update_value_by_key(key="smtp_password", value=value)

    @property
    def smtp_from(self):
        return self._smtp_from

    @smtp_from.setter
    def smtp_from(self, value):
        self._smtp_from = value
        self._update_value_by_key(key="smtp_from", value=value)

    @property
    def ssh_server_hostname(self):
        return self._ssh_server_hostname

    @ssh_server_hostname.setter
    def ssh_server_hostname(self, value):
        self._ssh_server_hostname = value
        self._update_value_by_key(key="ssh_server_hostname", value=value)

    @property
    def ssh_server_port(self):
        return int(self._ssh_server_port)

    @ssh_server_port.setter
    def ssh_server_port(self, value):
        self._ssh_server_port = value
        self._update_value_by_key(key="ssh_server_port", value=value)

    @property
    def ssh_server_listen_port(self):
        return int(self._ssh_server_listen_port)

    @ssh_server_listen_port.setter
    def ssh_server_listen_port(self, value):
        self._ssh_server_listen_port = value
        self._update_value_by_key(key="ssh_server_listen_port", value=value)

    @property
    def ssh_user_key(self):
        return self._ssh_user_key

    @ssh_user_key.setter
    def ssh_user_key(self, value):
        self._ssh_user_key = value
        self._update_value_by_key(key="ssh_user_key", value=value)

    @property
    def cloud_identifier(self):
        return self._cloud_identifier

    @cloud_identifier.setter
    def cloud_identifier(self, value):
        self._cloud_identifier = value
        self._update_value_by_key(key="cloud_identifier", value=value)

    @property
    def cloud_server_url(self):
        return self._cloud_server_url

    @cloud_server_url.setter
    def cloud_server_url(self, value):
        self._cloud_server_url = value
        self._update_value_by_key(key="cloud_server_url", value=value)

    def _update_value_by_key(self, key=None, value=None) -> bool:
        cursor = self._db_conn.cursor()
        cursor.execute('''UPDATE parameters SET
                        value = ?
                        WHERE key = ?''', (value, key))
        self._db_conn.commit()
        if cursor.rowcount == 1:
            _log.debug(f'Parameter {key} update: {value}')
            return True
        _log.debug(f'unable parameter {key} update: {value}')
        try:
            cursor.execute('''INSERT INTO parameters
                            (value, key)
                            VALUES (?,?)''', (value, key))
            self._db_conn.commit()
        except IntegrityError:
            _log.debug(f'unable parameter {key} insert: {value}')
            return False
        else:
            _log.debug(f'Parameter {key} insert: {value}')
            return True

    def _load_all(self):
        cursor = self._db_conn.cursor()
        cursor.execute("SELECT * from parameters")
        for row in cursor:
            attr_name = "_" + row['key']
            setattr(self, attr_name, row['value'])
