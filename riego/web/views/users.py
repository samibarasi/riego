from typing import Any, Dict
import aiohttp_jinja2
from aiohttp import web

from sqlite3 import IntegrityError
from riego.db import get_db
from riego.web.security import raise_permission


from logging import getLogger
_log = getLogger(__name__)

router = web.RouteTableDef()


def setup_routes_users(app):
    app.add_routes(router)


@ router.get("/users", name='users')
@ aiohttp_jinja2.template("users/index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission='superuser')
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM users')
    items = cursor.fetchall()
    get_db().conn.commit()
    return {"items": items}


@ router.get("/users/new", name='users_new')
@ aiohttp_jinja2.template("users/new.html")
async def new(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission='superuser')
    return {}


@ router.post("/users/new")
async def new_apply(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission='superuser')
    item = await request.post()
    try:
        with get_db().conn:
            cursor = get_db().conn.execute(
                ''' INSERT INTO users
                (identity, password,
                full_name, email,
                permission_id, is_superuser,
                is_disabled, remember_me)
                VALUES (?, ?, ?, ?, ?, ?) ''',
                (item['identity'], item['password'],
                 item['full_name'], item['email'],
                 item['permission_id'], item['is_superuser'],
                 item['is_disabled'], item['remember_me']))
    except IntegrityError as e:
        _log.debug(f'users add: {e}')
        raise web.HTTPSeeOther(request.app.router['users_new'].url_for())
    else:
        item_id = str(cursor.lastrowid)
        raise web.HTTPSeeOther(
            request.app.router['users_item_view'].url_for(item_id=item_id))
    return {}  # not reached


@ router.get("/users/{item_id}", name='users_item_view')
@ aiohttp_jinja2.template("users/view.html")
async def view(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission='superuser')
    item_id = request.match_info["item_id"]
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id=?', (item_id,))
    item = cursor.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(request.app.router['users'].url_for())
    return {"item": item}


@ router.get("/users/{item_id}/edit", name='users_item_edit')
@ aiohttp_jinja2.template("users/edit.html")
async def edit(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission='superuser')
    item_id = request.match_info["item_id"]
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id=?', (item_id,))
    item = cursor.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(request.app.router['users'].url_for())
    return {"item": item}


@ router.post("/users/{item_id}/edit")
async def edit_apply(request: web.Request) -> web.Response:
    await raise_permission(request, permission='superuser')
    item_id = request.match_info["item_id"]
    item = await request.post()
    try:
        with get_db().conn:
            get_db().conn.execute(
                '''UPDATE users
                   SET identity = ?, password = ?,
                   full_name = ?, email = ?,
                   permission_id = ?, is_superuser = ?,
                   is_disabled = ?, remember_me = ?
                   WHERE id = ? ''',
                (item['identity'], item['password'],
                 item['full_name'], item['email'],
                 item['permission_id'], item['is_superuser'],
                 item['is_disabled'], item['remember_me'],
                 item_id))
    except IntegrityError as e:
        _log.debug(f'box.view edit: {e}')
        raise web.HTTPSeeOther(
            request.app.router['users_item_edit'].url_for(item_id=item_id))
    else:
        raise web.HTTPSeeOther(
            request.app.router['users_item_view'].url_for(item_id=item_id))
    return {}  # Not reached


@ router.get("/users/{item_id}/delete", name='users_item_delete')
async def delete(request: web.Request) -> web.Response:
    await raise_permission(request, permission='superuser')
    item_id = request.match_info["item_id"]
    try:
        with get_db().conn:
            get_db().conn.execute(
                'DELETE FROM users WHERE id = ?',
                (item_id,))
    except IntegrityError as e:
        _log.debug(f'users  delete: {e}')
    raise web.HTTPSeeOther(request.app.router['users'].url_for())
    return {}  # Not reached
