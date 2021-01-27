from riego.web.dashboard.views import dashboard_index

import riego.web.system.views
import riego.web.boxes.views
import riego.web.valves.views

routes = [
    ('GET', '/',                    dashboard_index,      'dashboard_index'),
]


def setup_routes(app):
    global routes

    for route in routes:
        app.router.add_route(route[0], route[1], route[2], name=route[3])

    app.router.add_static('/static', app['options'].http_server_static_dir,
                          name='static', show_index=True)

    riego.web.system.views.register_router(app)
    riego.web.boxes.views.register_router(app)
    riego.web.valves.views.register_router(app)
