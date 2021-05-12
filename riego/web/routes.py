import os
import sys

import aiohttp_cors

from riego.web.views.dashboard import Dashboard
from riego.web.views.boxes import setup_routes_boxes
from riego.web.views.valves import setup_routes_valves
from riego.web.views.events import setup_routes_events
from riego.web.views.system import setup_routes_system
from riego.web.views.users import setup_routes_users
from riego.web.views.api import setup_routes_api

from riego.web.security import setup_routes_security


def setup_routes(app=None, options=None):
    dashboard = Dashboard(app)

    routes = [
        ('GET', '/',   dashboard.index,      'home'),
    ]

    for route in routes:
        app.router.add_route(route[0], route[1], route[2], name=route[3])

    app.router.add_static('/static', options.http_server_static_dir,
                          name='static', show_index=True)

    app.router.add_static('/frontend', os.path.join(os.path.dirname(__file__), 'frontend'),
                          name='frontend', show_index=True)

    setup_routes_boxes(app)
    setup_routes_valves(app)
    setup_routes_events(app)
    setup_routes_system(app)
    setup_routes_security(app)

    setup_routes_users(app)
    setup_routes_api(app)

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)
