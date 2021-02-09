from typing import Any, Dict
import aiohttp_jinja2
from aiohttp import web

from sqlite3 import IntegrityError
from riego.db import get_db
from riego.mqtt import get_mqtt

from logging import getLogger
_log = getLogger(__name__)

router = web.RouteTableDef()


def setup_routes_boxes(app):
    app.add_routes(router)


@router.get("/boxes")
@aiohttp_jinja2.template("boxes/index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    c = get_db().conn.cursor()
    c.execute('SELECT * FROM boxes')
    items = c.fetchall()
    get_db().conn.commit()
    return {"items": items}


@router.get("/boxes/new")
@aiohttp_jinja2.template("boxes/new.html")
async def new(request: web.Request) -> Dict[str, Any]:
    return {}


@router.post("/boxes/new")
@aiohttp_jinja2.template("boxes/edit.html")
async def new_apply(request: web.Request) -> Dict[str, Any]:
    item = await request.post()
    try:
        with get_db().conn:
            cursor = get_db.conn.execute(
                ''' INSERT INTO boxes
                (topic, name, remark)
                VALUES (?, ?, ?) ''',
                (item['topic'], item['name'], item['remark']))
    except IntegrityError as e:
        _log.debug(f'box.view add: {e}')
        raise web.HTTPSeeOther(location="/boxes/new")
    else:
        item_id = cursor.lastrowid
        raise web.HTTPSeeOther(location=f"/boxes/{item_id}")
    return {}  # not reached


@router.get("/boxes/{item_id}")
@aiohttp_jinja2.template("boxes/view.html")
async def view(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    c = get_db().conn.cursor()
    c.execute('SELECT * FROM boxes WHERE id=?', (item_id,))
    item = c.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(location="/boxes")
    return {"item": item}


@router.get("/boxes/{item_id}/edit")
@aiohttp_jinja2.template("boxes/edit.html")
async def edit(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    c = get_db().conn.cursor()
    c.execute('SELECT * FROM boxes WHERE id=?', (item_id,))
    item = c.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(location="/boxes")
    return {"item": item}


@router.post("/boxes/{item_id}/edit")
async def edit_apply(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    item = await request.post()
    try:
        with get_db().conn:
            get_db().conn.execute(
                ''' UPDATE boxes
                    SET _name = ?, remark = ?
                    WHERE id = ? ''',
                (item['name'], item['remark'], item_id))
    except IntegrityError as e:
        _log.debug(f'box.view edit: {e}')
        raise web.HTTPSeeOther(location=f"/boxes/{item_id}/edit")
    else:
        raise web.HTTPSeeOther(location=f"/boxes/{item_id}")
    return {}  # Not reached


@router.get("/boxes/{item_id}/delete")
async def delete(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    # TODO We should generate the mMQTT-message from a trigger
    # from database

    try:
        c = get_db().conn.cursor()
        c.execute('SELECT * FROM boxes WHERE id=?', (item_id,))
        item = c.fetchone()
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
        _log.debug(f'box.view delete: {e}')
    raise web.HTTPSeeOther(location="/boxes")
    return {}  # Not reached
