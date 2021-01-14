from riego.web.dashboard.views import dashboard_index
from riego.web.system.views import system_index, system_check_update, system_do_update, system_restart, system_setup, system_event_log, system_exc


routes = [
    ('GET', '/',                    dashboard_index,      'dashboard_index'),
    ('GET', '/system',              system_index,         'system_index'),
    ('GET', '/system/check_update', system_check_update,  'system_check_update'),
    ('GET', '/system/do_update',    system_do_update,     'system_do_update'),
    ('GET', '/system/restart',      system_restart,       'system_restart'),
    ('GET', '/system/setup',        system_setup,         'system_setup'),
    ('GET', '/system/event_log',    system_event_log,     'system_event_log'),
    ('GET', '/exc',                 system_exc,           'system_exc'),
]


def setup_routes(app):
    global routes

    for route in routes:
        app.router.add_route(route[0], route[1], route[2], name=route[3])

    app.router.add_static('/static', app['options'].http_server_static_dir,
                          name='static', show_index=True)
