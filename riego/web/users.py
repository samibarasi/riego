from aiohttp_session import get_session
import bcrypt
from sqlite3 import IntegrityError
from aiohttp import web
import asyncio


class User():
    def __init__(self, request=None, db=None):
        self._request = request
        self._db = db

    async def passwd(self, password):
        session = await get_session(self._request)
        user_id = session.get('user_id')

        if user_id is None:
            return False

        if not session.get('is_full_auth'):
            return False

        password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt(12))

        try:
            with self._db.conn:
                self._db.conn.execute(
                    ''' UPDATE users
                    SET password = ?
                    WHERE id = ? ''',
                    (password, user_id))
        except IntegrityError:
            pass
        return True

    async def check_permission(self, permission=None):
        # Remember_me cookie beachten
        session = await get_session(self._request)
        user_id = session.get('user_id')
        if user_id is None:
            raise web.HTTPUnauthorized()
        cursor = self._db.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        self._db.conn.commit()
        if user is None:
            raise web.HTTPUnauthorized()
        if user['is_disabled']:
            raise web.HTTPUnauthorized()
        if user['is_superuser']:
            return True
        if permission is None:
            return True
        for item in user['permissions']:
            if permission == item:
                return True
        raise web.HTTPForbidden()

    async def is_remembered(self):
        # Remember_me cookie beachten
        session = await get_session(self._request)
        return session.get('is_remembered')

    async def is_full_auth(self):
        # Remember_me cookie beachten
        session = await get_session(self._request)
        return session.get('is_full_auth')

    async def get_user_id(self):
        # Remember_me cookie beachten
        session = await get_session(self._request)
        return session.get('user_id')

    async def get_user(self):
        session = await get_session(self._request)

        user_id = session.get('user_id')
        if user_id is None:
            session.pop('is_full_auth', None)
        else:
            cursor = self._db.conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            self._db.conn.commit()

        if session.get('is_full_auth') is not None:
            return user

        remember_me = self._request.cookie.get('remember_me')
        if remember_me is not None:
            cursor = self._db.conn.cursor()
            cursor.execute('SELECT * FROM users WHERE remember_me = ?',
                           (remember_me,))
            user = cursor.fetchone()
            self._db.conn.commit()
        if user is not None:
            session['is_remembered'] = True
            session['user_id'] = user['id']
            # TODO Cookie Livetime renew?
        else:
            # Normally not possible
            asyncio.sleep(3)
        return user
