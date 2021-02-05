import aiohttp_jinja2
from aiohttp import web

from sqlalchemy.orm import joinedload

from riego.model.events import Event


router = web.RouteTableDef()


@router.get("/events")
@aiohttp_jinja2.template('events/index.html')
async def system_event_log(request):
    session = request.app['db'].Session()
    items = session.query(Event).options(joinedload('valve').options(joinedload('box'))).all()
    session.close()
    return {'items': items}


def register_router(app):
    app.add_routes(router)
