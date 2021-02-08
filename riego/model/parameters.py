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

        self._start_time_1 = options.parameters_start_time_1
        self._max_duration = options.parameters_max_duartion
        self._smtp_hostname = options.parameters_smtp_hostname
        self._smtp_port = options.parameters_smtp_port
        self._smtp_security = options.parameters_smtp_security
        self._smtp_user = options.parameters_smtp_user
        self._smtp_password = options.parameters_smtp_password
        self._smtp_from = options.parameters_smtp_from

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
        return self._max_duration

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

    def _update_value_by_key(self, key=None, value=None):
        try:
            with self._db_conn:
                self._db_conn.execute(
                    'UPDATE parameters SET value = ? WHERE key = ?',
                    (value, key))
        except IntegrityError:
            pass
        try:
            with self._db_conn:
                self._db_conn.execute(
                    "INSERT INTO parameters (value, key) VALUES (?,?)",
                    (value, key))
        except IntegrityError:
            pass

    def _load_all(self):
        c = self._db_conn.cursor()
        c.execute("SELECT * from parameters")
        items = c.fetchall()
        self._db_conn.commit()
        for item in items:
            attr_name = "_" + item['key']
            if getattr(self, attr_name, None) is not None:
                setattr(self, attr_name, item['value'])
