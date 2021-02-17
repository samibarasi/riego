from aiohttp_session import get_session
from sqlite3 import IntegrityError
from riego.db import get_db
from aiohttp import web
import bcrypt
import secrets
import json

from logging import getLogger
_log = getLogger(__name__)


async def current_user_ctx_processor(request):
    websocket_auth = '''{"token": "", "sequence": ""}'''
    user = await get_user(request)
    if user is not None:
        websocket_auth = await create_websocket_auth(request, user=user)
    return {'user': user, 'websocket_auth': json.loads(websocket_auth)}


async def get_user(request):
    session = await get_session(request)
    db = get_db()
    user_id = session.get('user_id')
    if user_id is not None:
        cursor = db.conn.cursor()
        cursor.execute("""SELECT *, 'login' AS 'provider'
                          FROM users
                          WHERE id = ?""", (user_id,))
        user = cursor.fetchone()
        if user is None or user['is_disabled']:
            session.pop('user_id', None)
            return None
        return user

    remember_me = request.cookies.get('remember_me')
    if remember_me is not None:
        cursor = db.conn.cursor()
        cursor.execute("""SELECT *, 'cookie' AS 'provider'
                           FROM users
                           WHERE remember_me = ?""", (remember_me,))
        user = cursor.fetchone()
        if user is None:
            return None
        if user['is_disabled']:
            try:
                with db.conn:
                    db.conn.execute("""UPDATE users
                                       SET remember_me = ''
                                       WHERE id = ?""", (user['id'],))
            except IntegrityError:
                pass
            return None
        return user
    return None


async def check_permission(request, permission=None):
    user = await get_user(request)
    db = get_db()
    if user is None:
        return None
    if user['is_disabled']:
        return None
    if user['is_superuser']:
        return user
    if permission is None:
        return user

    cursor = db.conn.cursor()
    cursor.execute(
        'SELECT * FROM users_permissions WHERE user_id = ?', (user['id'],))
    for row in cursor:
        if row['name'] == permission:
            return user

    return None


async def raise_permission(request, permission=None):
    if await check_permission(request, permission=permission) is None:
        raise web.HTTPSeeOther(
            request.app.router['login'].url_for(
            ).with_query(
                {"redirect": str(request.rel_url)}
            )
        )


async def create_websocket_auth(request, user=None):
    if user is None:
        return None
    session_key = request.app['options'].session_key_websocket_auth
    db = get_db()
    session = await get_session(request)
    websocket_auth = session.get(session_key, '')
    if len(websocket_auth) > 0:
        return websocket_auth

    sequence = secrets.token_urlsafe()
    token = secrets.token_urlsafe()
    token_hash = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt())

    try:
        with db.conn:
            db.conn.execute('''INSERT INTO users_tokens
                                (sequence, hash, category, user_id)
                                VALUES (?, ?, ?, ?)''',
                            (sequence, token_hash, "websocket", user['id']))
    except IntegrityError as e:
        _log.error(f'Unable to insert token: {e}')
        return None
    websocket_auth = json.dumps({"sequence": sequence, "token": token})
    session[session_key] = websocket_auth
    return websocket_auth


async def delete_websocket_auth(request, user=None):
    db = get_db()
    session = await get_session(request)
    session_key = request.app['options'].session_key_websocket_auth
    if session is not None:
        session.pop(session_key, None)
    try:
        with db.conn:
            db.conn.execute('''DELETE FROM users_tokens
                               WHERE category = ? AND user_id = ?''',
                            ("websocket", user['id']))
    except IntegrityError:
        pass
    return None


async def create_remember_me_auth(request, response=None, user=None):
    pass


async def delete_remember_me_auth(request, response=None, user=None):
    pass


def password_hash(pw):
    return bcrypt.hashpw(pw, bcrypt.gensalt(12))


def password_check(pw, pw_hash):
    return bcrypt.checkpw(pw, pw_hash)
