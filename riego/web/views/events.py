import aiohttp_jinja2
from aiohttp import web

from riego.db import get_db
from riego.web.security import raise_permission


router = web.RouteTableDef()


def setup_routes_events(app):
    app.add_routes(router)


@router.get("/events", name='events')
@aiohttp_jinja2.template('events/index.html')
async def event_index(request):
    await raise_permission(request, permission=None)
    cursor = get_db().conn.cursor()
    cursor.execute('''SELECT events.*, valves.name
                FROM events, valves
                WHERE events.valve_id = valves.id
                ORDER BY events.created_at DESC''')
    items = cursor.fetchall()
    get_db().conn.commit()
    return {'items': items}


@router.get("/events/{item_id}/filter", name='events_item_filter')
@aiohttp_jinja2.template('events/index.html')
async def event_filter(request):
    await raise_permission(request, permission=None)
    item_id = request.match_info["item_id"]
    cursor = get_db().conn.cursor()
    cursor.execute('''SELECT events.*, valves.name
                FROM events, valves
                WHERE events.valve_id = valves.id
                AND valves.id = ?
                ORDER BY events.created_at DESC''', (item_id,))
    items = cursor.fetchall()
    get_db().conn.commit()
    return {'items': items}
