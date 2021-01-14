from riego.web.main.views import main_index, exception_handler, main_system
from riego.web.dashboard.views import dashboard_index, dashboard_ws


routes = [
    ('GET', '/',                main_index,         'main_index'),
    ('GET', '/system',          main_system,        'main_system'),
    ('GET', '/dashboard',       dashboard_index,    'dashboard_index'),
    ('GET', '/dashboard/ws',    dashboard_ws,       'dashboard_ws'),
    ('GET', '/exc',             exception_handler,  'exc_example'),
]


def setup_routes(app):
    global routes

    for route in routes:
        app.router.add_route(route[0], route[1], route[2], name=route[3])

    app.router.add_static('/static', app['options'].http_server_static_dir,
                          name='static', show_index=True)
