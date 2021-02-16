from typing import Any, Dict
import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from sqlite3 import IntegrityError
from riego.db import get_db
from riego.web.users import User
import secrets
import bcrypt
import asyncio

from logging import getLogger
_log = getLogger(__name__)

router = web.RouteTableDef()


def setup_routes_users(app):
    app.add_routes(router)


@router.get("/login", name='login')
@aiohttp_jinja2.template("users/login.html")
async def login(request: web.Request) -> Dict[str, Any]:
    redirect = request.rel_url.query.get("redirect", "")
    csrf_token = secrets.token_urlsafe()
    session = await get_session(request)
    session['csrf_token'] = csrf_token
    return {'csrf_token': csrf_token, 'redirect': redirect}


@router.post("/login")
async def login_apply(request: web.Request) -> Dict[str, Any]:
    form = await request.post()
    session = await get_session(request)
    if session.get('csrf_token') != form['csrf_token']:
        await asyncio.sleep(2)
        raise web.HTTPUnauthorized()

    if form.get('identity') is None:
        await asyncio.sleep(2)
        raise web.HTTPSeeOther(request.app.router['login'].url_for())

    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM users WHERE identity = ?',
                   (form['identity'],))
    user = cursor.fetchone()
    get_db().conn.commit()

    if user is None or user['is_disabled']:
        await asyncio.sleep(2)
        raise web.HTTPSeeOther(request.app.router['login'].url_for())
    if not bcrypt.checkpw(form['password'].encode('utf8'), user['password']):
        await asyncio.sleep(2)
        raise web.HTTPSeeOther(request.app.router['login'].url_for())

    session['user_id'] = user['id']
    session['is_full_auth'] = True

    location = form.get('redirect')
    if location is None or location == '':
        location = request.app.router['dashboard_index'].url_for()
    response = web.HTTPSeeOther(location=location)
    if form.get('remember_me') is not None:
        remember_me = secrets.token_urlsafe(32)
        try:
            with get_db().conn:
                get_db().conn.execute(
                    ''' UPDATE users
                    SET remember_me = ?
                    WHERE id = ? ''',
                    (remember_me, user['id']))
        except IntegrityError:
            pass
        response.set_cookie("remember_me", remember_me,
                            max_age=7776000,
                            httponly=True,
                            samesite='strict')
    return response


@router.get("/logout", name='logout')
async def logout(request: web.Request) -> Dict[str, Any]:
    session = await get_session(request)
    session.pop('user_id', None)
    session.pop('is_remembered', None)
    session.pop('is_full_auth', None)
    response = web.HTTPSeeOther(request.app.router['login'].url_for())
    response.set_cookie('remember_me', '',
                        expires='Thu, 01 Jan 1970 00:00:00 GMT')
    return response


@router.get("/passwd", name='passwd')
@aiohttp_jinja2.template("users/passwd.html")
async def passwd(request: web.Request) -> Dict[str, Any]:
    return {}


@router.post("/passwd")
async def passwd_apply(request: web.Request) -> Dict[str, Any]:
    item = await request.post()
    user = User(request=request, db=get_db())
    if await user.passwd(item['new_password_1']):
        raise web.HTTPSeeOther(request.app.router['dashboard_index'].url_for())
    else:
        raise web.HTTPSeeOther(request.app.router['passwd'].url_for())
    return {}  # not reached


@router.get("/users", name='users')
@aiohttp_jinja2.template("users/index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM users')
    items = cursor.fetchall()
    get_db().conn.commit()
    return {"items": items}


@router.get("/users/new", name='users_new')
@aiohttp_jinja2.template("users/new.html")
async def new(request: web.Request) -> Dict[str, Any]:
    return {}


@router.post("/users/new")
async def new_apply(request: web.Request) -> Dict[str, Any]:
    item = await request.post()
    try:
        with get_db().conn:
            cursor = get_db().conn.execute(
                ''' INSERT INTO users
                (identity, password,
                permissions, is_superuser,
                is_disabled, remember_me)
                VALUES (?, ?, ?, ?, ?, ?) ''',
                (item['identity'], item['password'],
                 item['permissions'], item['is_superuser'],
                 item['is_disabled'], item['remember_me']))
    except IntegrityError as e:
        _log.debug(f'users add: {e}')
        raise web.HTTPSeeOther(request.app.router['users_new'].url_for())
    else:
        item_id = str(cursor.lastrowid)
        raise web.HTTPSeeOther(
            request.app.router['users_item_view'].url_for(item_id=item_id))
    return {}  # not reached


@router.get("/users/{item_id}", name='users_item_view')
@aiohttp_jinja2.template("users/view.html")
async def view(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id=?', (item_id,))
    item = cursor.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(request.app.router['users'].url_for())
    return {"item": item}


@router.get("/users/{item_id}/edit", name='users_item_edit')
@aiohttp_jinja2.template("users/edit.html")
async def edit(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id=?', (item_id,))
    item = cursor.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(request.app.router['users'].url_for())
    return {"item": item}


@router.post("/users/{item_id}/edit")
async def edit_apply(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    item = await request.post()
    try:
        with get_db().conn:
            get_db().conn.execute(
                '''UPDATE users
                   SET identity = ?, password = ?,
                   permissions = ?, is_superuser = ?,
                   is_disabled = ?, remember_me = ?
                   WHERE id = ? ''',
                (item['identity'], item['password'],
                 item['permissions'], item['is_superuser'],
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


@router.get("/users/{item_id}/delete", name='users_item_delete')
async def delete(request: web.Request) -> web.Response:
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
