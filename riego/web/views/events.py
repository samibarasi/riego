import aiohttp_jinja2
from aiohttp import web

from riego.db import get_db


router = web.RouteTableDef()


def setup_routes_events(app):
    app.add_routes(router)


@router.get("/events")
@aiohttp_jinja2.template('events/index.html')
async def system_event_log(request):
    c = get_db().conn.cursor()
    c.execute('''SELECT events.*, valves.name
                FROM events, valves
                WHERE events.valve_id = valves.id
                ORDER BY events.created_at DESC''')
    items = c.fetchall()
    get_db().conn.commit()
    return {'items': items}
