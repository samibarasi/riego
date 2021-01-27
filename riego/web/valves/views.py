from typing import Any, Dict
import aiohttp_jinja2
from aiohttp import web

router = web.RouteTableDef()


@router.get("/valves")
@aiohttp_jinja2.template("valves/index.html")
async def index_box(request: web.Request) -> Dict[str, Any]:
    valves = request.app['valves']
    items = await valves.fetch_all()
    return {"items": items}


@router.get("/valves/new")
@aiohttp_jinja2.template("valves/new.html")
async def new_box(request: web.Request) -> Dict[str, Any]:
    return {}


@router.post("/valves/new")
@aiohttp_jinja2.template("valves/edit.html")
async def new_box_apply(request: web.Request) -> Dict[str, Any]:
    valves = request.app['valves']
    item = await request.post()
    item_id = await valves.insert(item)
    if item_id is None:
        raise web.HTTPSeeOther(location="/valves/new")
    else:
        raise web.HTTPSeeOther(location=f"/valves/{item_id}")
    return {}


@router.get("/valves/{item_id}")
@aiohttp_jinja2.template("valves/view.html")
async def view_box(request: web.Request) -> Dict[str, Any]:
    valves = request.app['valves']
    item_id = request.match_info["item_id"]
    item = await valves.fetch_one_by_id(item_id)
    if item is None:
        raise web.HTTPSeeOther(location="/valves")
    return {"item": item}


@router.get("/valves/{item_id}/edit")
@aiohttp_jinja2.template("valves/edit.html")
async def edit_box(request: web.Request) -> Dict[str, Any]:
    valves = request.app['valves']
    item_id = request.match_info["item_id"]
    item = await valves.fetch_one_by_id(item_id)
    if item is None:
        raise web.HTTPSeeOther(location="/valves")
    return {"item": item}


@router.post("/valves/{item_id}/edit")
async def edit_box_apply(request: web.Request) -> web.Response:
    valves = request.app['valves']
    item_id = request.match_info["item_id"]
    item = await request.post()
    if await valves.update(item_id, item):
        raise web.HTTPSeeOther(location=f"/valves/{item_id}")
    else:
        raise web.HTTPSeeOther(location=f"/valves/{item_id}/edit")
    return {}


@router.get("/valves/{item_id}/delete")
async def delete_box(request: web.Request) -> web.Response:
    valves = request.app['valves']
    item_id = request.match_info["item_id"]
    await valves.delete(item_id)
    raise web.HTTPSeeOther(location="/valves")
    return {}


def register_router(app):
    app.add_routes(router)
