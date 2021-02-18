from typing import Any, Dict
import aiohttp_jinja2
from aiohttp import web
import asyncio

from sqlite3 import IntegrityError
from riego.db import get_db
from riego.mqtt import get_mqtt
from riego.web.security import raise_permission

from logging import getLogger
_log = getLogger(__name__)

router = web.RouteTableDef()


def setup_routes_boxes(app):
    app.add_routes(router)


@router.get("/boxes", name='boxes')
@aiohttp_jinja2.template("boxes/index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission=None)
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM boxes')
    items = cursor.fetchall()
    get_db().conn.commit()
    return {"items": items}


@router.get("/boxes/new", name='boxes_new')
@aiohttp_jinja2.template("boxes/new.html")
async def new(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission=None)
    return {}


@router.post("/boxes/new")
async def new_apply(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission=None)
    item = await request.post()
    try:
        with get_db().conn:
            cursor = get_db().conn.execute(
                ''' INSERT INTO boxes
                (topic, name, remark)
                VALUES (?, ?, ?) ''',
                (item['topic'], item['name'], item['remark']))
    except IntegrityError as e:
        _log.debug(f'box.view add: {e}')
        raise web.HTTPSeeOther(request.app.router['boxes_new'].url_for())
    else:
        item_id = str(cursor.lastrowid)
        raise web.HTTPSeeOther(
            request.app.router['boxes_item_view'].url_for(item_id=item_id))
    return {}  # not reached


@router.get("/boxes/{item_id}", name='boxes_item_view')
@aiohttp_jinja2.template("boxes/view.html")
async def view(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission=None)
    item_id = request.match_info["item_id"]
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM boxes WHERE id=?', (item_id,))
    item = cursor.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(request.app.router['boxes'].url_for())
    return {"item": item}


@router.get("/boxes/{item_id}/edit", name='boxes_item_edit')
@aiohttp_jinja2.template("boxes/edit.html")
async def edit(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission=None)
    item_id = request.match_info["item_id"]
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM boxes WHERE id=?', (item_id,))
    item = cursor.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(request.app.router['boxes'].url_for())
    return {"item": item}


@router.post("/boxes/{item_id}/edit")
async def edit_apply(request: web.Request) -> web.Response:
    await raise_permission(request, permission=None)
    item_id = request.match_info["item_id"]
    item = await request.post()
    try:
        with get_db().conn:
            get_db().conn.execute(
                ''' UPDATE boxes
                    SET name = ?, remark = ?
                    WHERE id = ? ''',
                (item['name'], item['remark'], item_id))
    except IntegrityError as e:
        _log.debug(f'box.view edit: {e}')
        raise web.HTTPSeeOther(
            request.app.router['boxes_item_edit'].url_for(item_id=item_id))
    else:
        raise web.HTTPSeeOther(
            request.app.router['boxes_item_view'].url_for(item_id=item_id))
    return {}  # Not reached


@router.get("/boxes/{item_id}/delete", name='boxes_item_delete')
async def delete(request: web.Request) -> web.Response:
    await raise_permission(request, permission=None)
    item_id = request.match_info["item_id"]
    # TODO We should generate the mMQTT-message from a trigger
    # from database

    try:
        cursor = get_db().conn.cursor()
        cursor.execute('SELECT * FROM boxes WHERE id=?', (item_id,))
        item = cursor.fetchone()
        get_db().conn.commit()
    except IntegrityError:
        pass
    else:
        topic = 'tele/{}/LWT'.format(item['topic'])
        get_mqtt().client.publish(topic, retain=True)

    try:
        with get_db().conn:
            get_db().conn.execute(
                'DELETE FROM boxes WHERE id = ?',
                (item_id,))
    except IntegrityError as e:
        _log.debug(f'box.delete: {e}')
    raise web.HTTPSeeOther(request.app.router['boxes'].url_for())
    return {}  # Not reached


@router.get("/boxes/{item_id}/restart", name='boxes_item_restart')
async def restart(request: web.Request) -> web.Response:
    await raise_permission(request, permission=None)
    item_id = request.match_info["item_id"]
    try:
        cursor = get_db().conn.cursor()
        cursor.execute('SELECT * FROM boxes WHERE id=?', (item_id,))
        item = cursor.fetchone()
        get_db().conn.commit()
    except IntegrityError:
        pass
    else:
        topic = 'cmnd/{}/Restart'.format(item['topic'])
        message = '1'
        get_mqtt().client.publish(topic, message)
        await asyncio.sleep(10)
    raise web.HTTPSeeOther(
        request.app.router['boxes_item_view'].url_for(item_id=item_id))
    return {}  # Not reached
