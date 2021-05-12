from sqlite3 import IntegrityError
import asyncio
import bcrypt
import secrets

from typing import Any, Dict
from aiohttp import web
from aiohttp_session import get_session

from riego.db import query_db
from riego.web.security import raise_permission

from logging import getLogger
_log = getLogger(__name__)

router = web.RouteTableDef()

def setup_routes_api(app):
    app.add_routes(router)

@router.get("/api/users", name="api_users")
async def index(request: web.Request) -> Dict[str, Any]:
    #await raise_permission(request, permission='')
    my_query = query_db("SELECT id, identity, datetime(created_at) created_at FROM users")
    res = { "items": my_query }
    return web.json_response(my_query)

@router.get("/api/user/{item_id}", name='api_user')
async def view(request: web.Request) -> Dict[str, Any]:
    #await raise_permission(request, permission='superuser')
    item_id = request.match_info["item_id"]
    item = query_db('SELECT id, identity, is_superuser, is_disabled, remember_me, created_at FROM users WHERE id=?', (item_id,), True)
    return web.json_response(item)


@ router.post("/api/login")
async def login_apply(request: web.Request):
    form = await request.post()
    session = await get_session(request)
    # if session.get('csrf_token') != form['csrf_token']:
    #     # Normally not possible
    #     await asyncio.sleep(2)
    #     raise web.HTTPUnauthorized()

    if form.get('identity') is None:
        await asyncio.sleep(2)
        #raise web.HTTPSeeOther(request.app.router['login'].url_for())
        return web.json_response({"status": "error", "message": "Unauthorized. Please Log in."}, status=401, reason="identity is missing")
        

    # cursor = get_db().conn.cursor()
    # cursor.execute("""SELECT *, 'login' AS provider
    #                 FROM users
    #                 WHERE identity = ?""", (form['identity'],))
    #user = cursor.fetchone()
    user = query_db("""SELECT *, 'login' AS provider
                    FROM users
                    WHERE identity = ?""", (form['identity'],), True)

    if (
        user is None or
        user['is_disabled'] or
        user['password'] is None or
        not len(user['password'])
    ):
        await asyncio.sleep(2)
        #raise web.HTTPSeeOther(request.app.router['login'].url_for())
        return web.json_response({"status": "error", "message": "Unauthorized. Please Log in."}, status=401, reason="identity unknown or password is incorrect")

    if not bcrypt.checkpw(form['password'].encode('utf-8'),
                          user['password'].encode('utf-8')):
        await asyncio.sleep(2)
        #raise web.HTTPSeeOther(request.app.router['login'].url_for())
        return web.json_response({"status": "error", "message": "Unauthorized. Please Log in."}, status=401, reason="identity unknown or password is incorrect")


    session['user_id'] = user['id']

    response = web.json_response({"status": "success", "message": "Successfully logged in."})

    # location = form.get('redirect')
    # if location is None or location == '':
    #     location = request.app.router['home'].url_for()
    # response = web.HTTPSeeOther(location=location)
# TODO use create_remember_me
    if form.get('remember_me') is not None:
        remember_me = secrets.token_urlsafe()
        try:
            # with get_db().conn:
            #     get_db().conn.execute(
            #         '''UPDATE users
            #            SET remember_me = ?
            #            WHERE id = ? ''',
            #         (remember_me, user['id']))
            query_db('''UPDATE users
                       SET remember_me = ?
                       WHERE id = ? ''', (remember_me, user['id']))
        except IntegrityError:
            pass
        response.set_cookie("remember_me", remember_me,
                            max_age=request.app['options'].max_age_remember_me,
                            httponly=True,
                            samesite='strict')
    return response
