from typing import Any, Dict
import aiohttp_jinja2
from aiohttp import web

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from riego.model.valves import Valve

router = web.RouteTableDef()


@router.get("/valves")
@aiohttp_jinja2.template("valves/index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    session = request.app['db'].Session()
    items = session.query(Valve).all()
    session.close()
    return {"items": items}


@router.get("/valves/new")
@aiohttp_jinja2.template("valves/new.html")
async def new(request: web.Request) -> Dict[str, Any]:
    return {}


@router.post("/valves/new")
@aiohttp_jinja2.template("valves/edit.html")
async def new_apply(request: web.Request) -> Dict[str, Any]:
    item = await request.post()
    session = request.app['db'].Session()
    # TODO Form validation for every field
    valve = Valve(**item)
    session.add(valve)
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        session.close()
        request.app['log'].debug(f'valve.view add: {e}')
        raise web.HTTPSeeOther(location="/valves/new")
    else:
        item_id = valve.id
        session.close()
        raise web.HTTPSeeOther(location=f"/valves/{item_id}")
    return {}  # Not reached


@router.get("/valves/{item_id}")
@aiohttp_jinja2.template("valves/view.html")
async def view(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    session = request.app['db'].Session()
    item = session.query(Valve).options(joinedload('box')).get(item_id)
    session.close()
    if item is None:
        raise web.HTTPSeeOther(location="/valves")
    return {"item": item}


@router.get("/valves/{item_id}/edit")
@aiohttp_jinja2.template("valves/edit.html")
async def edit(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    session = request.app['db'].Session()
    item = session.query(Valve).get(item_id)
    session.close()
    if item is None:
        raise web.HTTPSeeOther(location="/valves")
    return {"item": item}


@router.post("/valves/{item_id}/edit")
async def edit_apply(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    item = await request.post()
    session = request.app['db'].Session()
    # TODO Form validation for every field
    session.query(Valve).filter(Valve.id == item_id).update(item, False)
    try:
        session.commit()
    except IntegrityError as e:
        session.close()
        request.app['log'].debug(f'valve.view edit: {e}')
        raise web.HTTPSeeOther(location=f"/valves/{item_id}")
    else:
        session.rollback()
        session.close()
        raise web.HTTPSeeOther(location=f"/valves/{item_id}/edit")
    return {}  # Not reached


@router.get("/valves/{item_id}/delete")
async def delete(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    session = request.app['db'].Session()
    item = session.query(Valve).get(item_id)
    session.delete(item)
    try:
        session.commit()
    except IntegrityError as e:
        request.app['log'].debug(f'valve.view delete: {e}')
    session.close()

    raise web.HTTPSeeOther(location="/valves")
    return {}  # Not reached


def register_router(app):
    app.add_routes(router)
