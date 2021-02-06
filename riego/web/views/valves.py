from typing import Any, Dict
import aiohttp_jinja2
from aiohttp import web

from sqlite3 import IntegrityError
from riego.db import get_db

from logging import getLogger
_log = getLogger(__name__)

router = web.RouteTableDef()


def setup_routes_valves(app):
    app.add_routes(router)


@router.get("/valves")
@aiohttp_jinja2.template("valves/index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    c = get_db().conn.cursor()
    c.execute('SELECT * FROM valves')
    items = c.fetchall()
    get_db().conn.commit()
    return {"items": items}


@router.get("/valves/new")
@aiohttp_jinja2.template("valves/new.html")
async def new(request: web.Request) -> Dict[str, Any]:
    return {}


@router.post("/valves/new")
@aiohttp_jinja2.template("valves/edit.html")
async def new_apply(request: web.Request) -> Dict[str, Any]:
    item = await request.post()
    try:
        with get_db().conn:
            cursor = get_db.conn.execute(
                ''' INSERT INTO valves
                (name, channel_nr, box_id)
                VALUES (?, ?, ?) ''',
                (item['name'], item['channel_nr'], item['box_id']))
    except IntegrityError as e:
        _log.debug(f'box.view add: {e}')
        raise web.HTTPSeeOther(location="/valves/new")
    else:
        item_id = cursor.lastrowid
        raise web.HTTPSeeOther(location=f"/valves/{item_id}")
    return {}  # not reached


@router.get("/valves/{item_id}")
@aiohttp_jinja2.template("valves/view.html")
async def view(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    c = get_db().conn.cursor()
    c.execute('''SELECT valves.*,
                boxes.name AS box_name,
                boxes.topic AS box_topic
                FROM valves, boxes
                WHERE valves.box_id = boxes.id AND valves.id=?''', (item_id,))
    item = c.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(location="/valves")
    return {"item": item}


@router.get("/valves/{item_id}/edit")
@aiohttp_jinja2.template("valves/edit.html")
async def edit(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    c = get_db().conn.cursor()
    c.execute('SELECT * FROM valves WHERE id=?', (item_id,))
    item = c.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(location="/valves")
    return {"item": item}


@router.post("/valves/{item_id}/edit")
async def edit_apply(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    item = await request.post()
    try:
        with get_db().conn:
            get_db().conn.execute(
                ''' UPDATE valves
                    SET name = ?, remark = ?,
                    duration = ?, interval = ?,
                    is_running = ? , is_enabled= ?,
                    is_hidden = ?,  prio = ? 
                    WHERE id = ? ''',
                (item['name'], item['remark'],
                 item['duration'], item['interval'],
                 item['is_running'], item['is_enabled'],
                 item['is_hidden'], item['prio'], item_id))
    except IntegrityError as e:
        _log.debug(f'box.view edit: {e}')
        raise web.HTTPSeeOther(location=f"/valves/{item_id}/edit")
    else:
        raise web.HTTPSeeOther(location=f"/valves/{item_id}")
    return {}  # Not reached


@router.get("/valves/{item_id}/delete")
async def delete(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    try:
        with get_db().conn:
            get_db().conn.execute(
                'DELETE FROM valves WHERE id = ?',
                (item_id,))
    except IntegrityError as e:
        _log.debug(f'box.view delete: {e}')
    raise web.HTTPSeeOther(location="/valves")
    return {}  # Not reached
