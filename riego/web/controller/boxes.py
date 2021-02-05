from typing import Any, Dict
import aiohttp_jinja2
from aiohttp import web

from sqlalchemy.exc import IntegrityError
from riego.model.boxes import Box

router = web.RouteTableDef()


@router.get("/boxes")
@aiohttp_jinja2.template("boxes/index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    session = request.app['db'].Session()
    items = session.query(Box).all()
    session.close()
    return {"items": items}


@router.get("/boxes/new")
@aiohttp_jinja2.template("boxes/new.html")
async def new(request: web.Request) -> Dict[str, Any]:
    return {}


@router.post("/boxes/new")
@aiohttp_jinja2.template("boxes/edit.html")
async def new_apply(request: web.Request) -> Dict[str, Any]:
    item = await request.post()
    session = request.app['db'].Session()
    # TODO Form validation for every field
    box = Box(**item)
    session.add(box)
    try:
        session.commit()
    except IntegrityError as e:
        session.rollbacl()
        session.close()
        request.app['log'].debug(f'box.view add: {e}')
        raise web.HTTPSeeOther(location="/boxes/new")
    else:
        item_id = box.id
        session.close()
        raise web.HTTPSeeOther(location=f"/boxes/{item_id}")
    return {}  # Not reached


@router.get("/boxes/{item_id}")
@aiohttp_jinja2.template("boxes/view.html")
async def view(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    session = request.app['db'].Session()
    item = session.query(Box).get(item_id)
    session.close()
    if item is None:
        raise web.HTTPSeeOther(location="/boxes")
    return {"item": item}


@router.get("/boxes/{item_id}/edit")
@aiohttp_jinja2.template("boxes/edit.html")
async def edit(request: web.Request) -> Dict[str, Any]:
    item_id = request.match_info["item_id"]
    session = request.app['db'].Session()
    item = session.query(Box).get(item_id)
    session.close()
    if item is None:
        raise web.HTTPSeeOther(location="/boxes")
    return {"item": item}


@router.post("/boxes/{item_id}/edit")
async def edit_apply(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    item = await request.post()
    session = request.app['db'].Session()
    # TODO Form validation for every field
    session.query(Box).filter(Box.id == item_id).update(item, False)
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        session.close()
        request.app['log'].debug(f'box.view edit: {e}')
        raise web.HTTPSeeOther(location=f"/boxes/{item_id}/edit")
    else:
        session.close()
        raise web.HTTPSeeOther(location=f"/boxes/{item_id}")
    return {}  # Not reached


@router.get("/boxes/{item_id}/delete")
async def delete(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    session = request.app['db'].Session()
    item = session.query(Box).get(item_id)
    session.delete(item)
    try:
        session.commit()
    except IntegrityError as e:
        request.app['log'].debug(f'box.view delete: {e}')
    session.close()

    raise web.HTTPSeeOther(location="/boxes")
    return {}  # Not reached


def register_router(app):
    app.add_routes(router)
