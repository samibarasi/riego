import asyncio
import configargparse
import pkg_resources
import os
from pathlib import Path
import socket

import logging
from logging.handlers import RotatingFileHandler

from riego.db import setup_db
from riego.mqtt import setup_mqtt
from riego.boxes import setup_boxes
from riego.valves import setup_valves
from riego.timer import setup_timer
from riego.model.parameters import setup_parameters


from riego.web.websockets import setup_websockets
from riego.web.routes import setup_routes
from riego.web.error_pages import setup_error_pages


from aiohttp import web
import jinja2
import aiohttp_jinja2
import aiohttp_debugtoolbar


from riego import __version__


def main():
    options = _get_options()

    _setup_logging(options=options)

    try:
        with open('riego.conf', 'xt') as f:
            for item in vars(options):
                f.write(f'# {item}={getattr(options, item)}\n')
    except IOError:
        pass

    if options.defaults:
        for item in vars(options):
            print(f'# {item}={getattr(options, item)}')
        exit(0)

    if options.version:
        print('Version: ', __version__)
        exit(0)

#    if sys.version_info >= (3, 8):
#        asyncio.DefaultEventLoopPolicy = asyncio.WindowsSelectorEventLoopPolicy  # noqa: E501

    if os.name == "posix":
        import uvloop  # pylint: disable=import-error
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    app = web.Application()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.on_cleanup.append(on_cleanup)

    app['version'] = __version__
    app['options'] = options

    websockets = setup_websockets(app=app, options=options)
    db = setup_db(options=options)
    parameters = setup_parameters(app=app, options=options, db=db)
    mqtt = setup_mqtt(app=app, options=options)
    setup_boxes(options=options, db=db, mqtt=mqtt)
    valves = setup_valves(options=options, db=db,
                          mqtt=mqtt, websockets=websockets)
    setup_timer(app=app, options=options, db=db,
                mqtt=mqtt, valves=valves, parameters=parameters)

    loader = jinja2.FileSystemLoader(options.http_server_template_dir)
    aiohttp_jinja2.setup(app,
                         loader=loader,
                         # enable_async=True,
                         # context_processors=[alert_ctx_processor],
                         )
    setup_routes(app)
    setup_error_pages(app)

    if options.enable_aiohttp_debug_toolbar:
        aiohttp_debugtoolbar.setup(
            app, check_host=False, intercept_redirects=False)

    main_app = web.Application()

    async def main_app_handler(request):
        raise web.HTTPSeeOther('/riego/')

    main_app.router.add_get('/', main_app_handler)
    main_app.add_subapp('/riego/', app)

    logging.getLogger(__name__).info("Start")

    web.run_app(main_app,
                host=options.http_server_bind_address,
                port=options.http_server_bind_port)


def _setup_logging(options=None):
    formatter = logging.Formatter(
        "%(asctime)s;%(levelname)s;%(name)s;%(message)s ")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    if options.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    file_handler = RotatingFileHandler(options.log_file, mode='a',
                                       maxBytes=options.log_max_bytes,
                                       backupCount=options.log_backup_count,
                                       encoding=None, delay=0)
    file_handler.setFormatter(formatter)
    Path(options.log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=level, handlers=[stream_handler, file_handler])

    logging.getLogger("gmqtt").setLevel(logging.ERROR)
    logging.getLogger("aiohttp.access").setLevel(logging.DEBUG)


def _get_options():
    p = configargparse.ArgParser(
        default_config_files=['/etc/riego/conf.d/*.conf', '~/.riego.conf',
                              'riego.conf'])
    p.add('-c', '--config', is_config_file=True, env_var='RIEGO_CONF',
          required=False, help='config file path')
    p.add('-d', '--db_filename', help='Path and name for DB file',
          default='db/riego.db')
    p.add('--db_migrations_dir',
          help='path to database migrations directory',
          default=pkg_resources.resource_filename('riego', 'migrations'))
    p.add('-l', '--log_file', help='Full path to logfile',
          default='log/riego.log')
    p.add('--log_max_bytes', help='Maximum Evet Log Size in bytes',
          default=1024*300, type=int)
    p.add('--log_backup_count', help='How many files to rotate',
          default=3, type=int)
    p.add('-m', '--mqtt_host', help='IP adress of mqtt host',
          default='127.0.0.1')
    p.add('-p', '--mqtt_port', help='Port of mqtt service',
          default=1883, type=int)
    p.add('--mqtt_client_id', help='Client ID for MQTT-Connection',
          default=f'riego_ctrl_{socket.gethostname()}')
    p.add('--mqtt_subscription_topic', help='MQTT Topic that we are listening',
          default='riego/#')
    p.add('--base_dir', help='Change only if you know what you are doing',
          default=Path(__file__).parent)
    p.add('--http_server_bind_address',
          help='http-server bind address', default='0.0.0.0')
    p.add('--http_server_bind_port', help='http-server bind port',
          default=8080, type=int)
    p.add('--http_server_static_dir',
          help='Serve static html files from this directory',
          default=pkg_resources.resource_filename('riego.web', 'static'))
    p.add('--http_server_template_dir',
          help='Serve template files from this directory',
          default=pkg_resources.resource_filename('riego.web', 'templates'))
    p.add('--websocket_path', help='url path for websocket',
          default="/ws")

    p.add('--time_format', help='Store and display time',
          default="%Y-%m-%d %H:%M:%S")
    p.add('--mqtt_cmnd_prefix', help='',
          default="cmnd")
    p.add('--mqtt_result_subscription', help='used by class valves',
          default="stat/+/RESULT")

    p.add('--mqtt_lwt_subscription', help='used by class boxes',
          default="tele/+/LWT")
    p.add('--mqtt_state_subscription', help='used by class boxes',
          default="tele/+/STATE")
    p.add('--mqtt_info1_subscription', help='used by class boxes',
          default="tele/+/INFO1")
    p.add('--mqtt_info2_subscription', help='used by class boxes',
          default="tele/+/INFO2")

    p.add('--mqtt_sensor_subscription', help='yet not used',
          default="tele/+/SENSOR")

    p.add('--mqtt_keyword_ON', help='',
          default="ON")
    p.add('--mqtt_keyword_OFF', help='',
          default="OFF")

    p.add('--parameters_smtp_hostname', default="smtp.gmail.com")
    p.add('--parameters_smtp_port', type=int, default=465)
    p.add('--parameters_smtp_security', default="use_tls=True")
    p.add('--parameters_smtp_user', default="user")
    p.add('--parameters_smtp_password', default="password")
    p.add('--parameters_smtp_from', default="riego@localhost")

    p.add('--parameters_start_time_1', default="19:00")
    p.add('--parameters_max_duartion', default="240")

    p.add('--enable_aiohttp_debug_toolbar', action='store_true')
    p.add('--enable_asyncio_debug', action='store_true')
    p.add('--enable_timer_dev_mode', action='store_true')

    p.add('-v', '--verbose', help='verbose', action='store_true')
    p.add('--version', help='Print version and exit', action='store_true')
    p.add('--defaults', help='Print options with default values and exit',
          action='store_true')

    options = p.parse_args()
    if options.verbose:
        print(p.format_values())

    return options


async def on_startup(app):
    logging.getLogger(__name__).debug("on_startup")
    if app['options'].enable_asyncio_debug:
        asyncio.get_event_loop().set_debug(True)


async def on_shutdown(app):
    logging.getLogger(__name__).debug("on_shutdown")


async def on_cleanup(app):
    logging.getLogger(__name__).debug("on_cleanup")
