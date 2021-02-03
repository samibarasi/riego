from riego.model.parameter import Parameter


class Parameters:
    def __init__(self, app):
        self._db = app['db']
        self._Parameter = Parameter()

    def get(self, key):
        c = self.db_conn.cursor()
        c.execute('SELECT * from parameters WHERE key=?',
                  (key,))
        ret = c.fetchone()
        c.close()
        if ret is not None:
            ret = (ret['value'])
        return ret

    def update(self, key, value):
        c = self.db_conn.cursor()
        c.execute('UPDATE parameters SET value=? WHERE key=?',
                  (value, key))
        self.db_conn.commit()
        c.close()

    def insert(self, key, value):
        c = self.db_conn.cursor()
        c.execute('INSERT INTO parameters (key,value) VALUES (?,?)',
                  (value, key))
        self.db_conn.commit()
        c.close()

    def delete(self, key):
        c = self.db_conn.cursor()
        c.execute('DELETE FROM parameters WHERE key=?',
                  (key,))
        self.db_conn.commit()
        c.close()
