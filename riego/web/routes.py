from riego.web.views.dashboard import Dashboard


from riego.web.views.boxes import register_router as setup_boxes
from riego.web.views.valves import register_router as setup_valves
from riego.web.views.events import register_router as setup_events
from riego.web.views.system import register_router as setup_system


def setup_routes(app):
    dashboard = Dashboard(app)

    routes = [
        ('GET', '/',   dashboard.index,      'dashboard_index'),
    ]

    for route in routes:
        app.router.add_route(route[0], route[1], route[2], name=route[3])

    app.router.add_static('/static', app['options'].http_server_static_dir,
                          name='static', show_index=True)

    setup_boxes(app)
    setup_valves(app)
    setup_events(app)
    setup_system(app)
