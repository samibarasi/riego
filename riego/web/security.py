from aiohttp_session import get_session
from sqlite3 import IntegrityError
from riego.db import get_db
from aiohttp import web
import bcrypt


async def current_user_ctx_processor(request):
    user = await get_user(request)
    return {'user': user}


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


def password_hash(pw):
    return bcrypt.hashpw(pw, bcrypt.gensalt(12))


def password_check(pw, pw_hash):
    return bcrypt.checkpw(pw, pw_hash)
