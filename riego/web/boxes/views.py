from typing import Any, AsyncIterator, Dict
import aiohttp_jinja2
from aiohttp import web

router = web.RouteTableDef()


@router.get("/boxes")
@aiohttp_jinja2.template("boxes/index.html")
async def index_box(request: web.Request) -> Dict[str, Any]:
    boxes = request.app['boxes']
    items = await boxes.fetch_all()
    return {"items": items}


@router.get("/boxes/new")
@aiohttp_jinja2.template("boxes/new.html")
async def new_box(request: web.Request) -> Dict[str, Any]:
    return {}


@router.post("/boxes/new")
@aiohttp_jinja2.template("boxes/edit.html")
async def new_box_apply(request: web.Request) -> Dict[str, Any]:
    boxes = request.app['boxes']
    item = await request.post()
    item_id = await boxes.insert(item)
    if item_id is None:
        raise web.HTTPSeeOther(location="/boxes/new")
    else:
        raise web.HTTPSeeOther(location=f"/boxes/{item_id}")


@router.get("/boxes/{item_id}")
@aiohttp_jinja2.template("boxes/view.html")
async def view_box(request: web.Request) -> Dict[str, Any]:
    boxes = request.app['boxes']
    item_id = request.match_info["item_id"]
    item = await boxes.fetch_one_by_id(item_id)
    if item is None:
        raise web.HTTPSeeOther(location="/boxes")
    return {"item": item}


@router.get("/boxes/{item_id}/edit")
@aiohttp_jinja2.template("boxes/edit.html")
async def edit_box(request: web.Request) -> Dict[str, Any]:
    boxes = request.app['boxes']
    item_id = request.match_info["item_id"]
    item = await boxes.fetch_one_by_id(item_id)
    if item is None:
        raise web.HTTPSeeOther(location="/boxes")
    return {"item": item}


@router.post("/boxes/{item_id}/edit")
async def edit_box_apply(request: web.Request) -> web.Response:
    boxes = request.app['boxes']
    item_id = request.match_info["item_id"]
    item = await request.post()
    if await boxes.update(item_id, item):
        raise web.HTTPSeeOther(location=f"/boxes/{item_id}")
    else:
        raise web.HTTPSeeOther(location=f"/boxes/{item_id}/edit")


@router.get("/boxes/{item_id}/delete")
async def delete_box(request: web.Request) -> web.Response:
    boxes = request.app['boxes']
    item_id = request.match_info["item_id"]
    await boxes.delete(item_id)
    raise web.HTTPSeeOther(location="/boxes")


def register_router(app):
    app.add_routes(router)
