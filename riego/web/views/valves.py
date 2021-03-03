from typing import Any, Dict
import aiohttp_jinja2
from aiohttp import web

from sqlite3 import IntegrityError
from riego.db import get_db
from riego.web.security import raise_permission

from logging import getLogger
_log = getLogger(__name__)

router = web.RouteTableDef()


def setup_routes_valves(app):
    app.add_routes(router)


@router.get("/valves", name='valves')
@aiohttp_jinja2.template("valves/index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission="")
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM valves')
    items = cursor.fetchall()
    get_db().conn.commit()
    return {"items": items}


@router.get("/valves/new", name='valves_new')
@aiohttp_jinja2.template("valves/new.html")
async def new(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission="")
    return {}


@router.post("/valves/new")
async def new_apply(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission="")
    item = await request.post()
    try:
        with get_db().conn:
            cursor = get_db().conn.execute(
                ''' INSERT INTO valves
                (name, channel_nr, box_id)
                VALUES (?, ?, ?) ''',
                (item['name'], item['channel_nr'], item['box_id']))
    except IntegrityError as e:
        _log.debug(f'box.view add: {e}')
        raise web.HTTPSeeOther(request.app.router['valves_new'].url_for())
    else:
        item_id = str(cursor.lastrowid)
        raise web.HTTPSeeOther(
            request.app.router['valves_item_view'].url_for(item_id=item_id))
    return {}  # not reached


@router.get("/valves/{item_id}", name='valves_item_view')
@aiohttp_jinja2.template("valves/view.html")
async def view(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission="")
    item_id = request.match_info["item_id"]
    cursor = get_db().conn.cursor()
    cursor.execute('''SELECT valves.*,
                boxes.name AS box_name,
                boxes.topic AS box_topic
                FROM valves, boxes
                WHERE valves.box_id = boxes.id AND valves.id=?''', (item_id,))
    item = cursor.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(request.app.router['valves'].url_for())
    return {"item": item}


@router.get("/valves/{item_id}/edit", name='valves_item_edit')
@aiohttp_jinja2.template("valves/edit.html")
async def edit(request: web.Request) -> Dict[str, Any]:
    await raise_permission(request, permission="")
    item_id = request.match_info["item_id"]
    cursor = get_db().conn.cursor()
    cursor.execute('SELECT * FROM valves WHERE id=?', (item_id,))
    item = cursor.fetchone()
    get_db().conn.commit()
    if item is None:
        raise web.HTTPSeeOther(request.app.router['valves'].url_for())
    return {"item": item}


@router.post("/valves/{item_id}/edit")
async def edit_apply(request: web.Request) -> web.Response:
    await raise_permission(request, permission="")
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
        raise web.HTTPSeeOther(
            request.app.router['valves_item_edit'].url_for(item_id=item_id))
    else:
        raise web.HTTPSeeOther(
            request.app.router['valves_item_view'].url_for(item_id=item_id))
    return {}  # Not reached


@router.get("/valves/{item_id}/delete", name='valves_item_delete')
async def delete(request: web.Request) -> web.Response:
    await raise_permission(request, permission="")
    item_id = request.match_info["item_id"]
    try:
        with get_db().conn:
            get_db().conn.execute(
                'DELETE FROM valves WHERE id = ?',
                (item_id,))
    except IntegrityError as e:
        _log.debug(f'valves delete: {e}')
    raise web.HTTPSeeOther(request.app.router['valves'].url_for())
    return {}  # Not reached
