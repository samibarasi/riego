import asyncio
import configargparse
import pkg_resources
import os
import sys
from pathlib import Path
import socket
import secrets

import logging
from logging.handlers import RotatingFileHandler

from riego.db import setup_db
from riego.mqtt import setup_mqtt
from riego.cloud import setup_cloud
from riego.boxes import setup_boxes
from riego.valves import setup_valves
from riego.timer import setup_timer
from riego.model.parameters import setup_parameters


from riego.web.websockets import setup_websockets
from riego.web.routes import setup_routes
from riego.web.error_pages import setup_error_pages
from riego.web.security import current_user_ctx_processor


from aiohttp import web
import jinja2
import aiohttp_jinja2
import aiohttp_debugtoolbar
from aiohttp_remotes import setup as setup_remotes, XForwardedRelaxed

from aiohttp_session import setup as session_setup
from aiohttp_session.memcached_storage import MemcachedStorage
import aiomcache

from riego import __version__

PRIMARY_INI_FILE = 'riego.conf'


async def on_startup(app):
    logging.getLogger(__name__).debug("on_startup")


async def on_shutdown(app):
    logging.getLogger(__name__).debug("on_shutdown")


async def on_cleanup(app):
    logging.getLogger(__name__).debug("on_cleanup")


def main():
    options = _get_options()

    _setup_logging(options=options)

    if sys.version_info >= (3, 8) and options.WindowsSelectorEventLoopPolicy:
        asyncio.DefaultEventLoopPolicy = asyncio.WindowsSelectorEventLoopPolicy  # noqa: E501

    if os.name == "posix":
        import uvloop  # pylint: disable=import-error
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    web.run_app(run_app(options=options),
                host=options.http_server_bind_address,
                port=options.http_server_bind_port,
                # access_log=_setup_access_log(options=options)
                )


async def run_app(options=None):
    loop = asyncio.get_event_loop()

    if options.enable_asyncio_debug_log:
        loop.set_debug(True)

    app = web.Application()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.on_cleanup.append(on_cleanup)

    app['version'] = __version__
    app['options'] = options

    db = setup_db(options=options)
    websockets = setup_websockets(app=app, db=db, options=options)
    parameters = setup_parameters(app=app, db=db, options=options)
    mqtt = setup_mqtt(app=app, options=options)
    setup_boxes(options=options, db=db, mqtt=mqtt)
    valves = setup_valves(options=options, db=db,
                          mqtt=mqtt, websockets=websockets)
    setup_timer(app=app, options=options, db=db,
                mqtt=mqtt, valves=valves, parameters=parameters)
    setup_cloud(app=app, parameters=parameters, options=options)
    
    mcache = aiomcache.Client(options.memcached_host, options.memcached_port)
    session_setup(app, MemcachedStorage(mcache))

    async def mcache_shutdown(app):
        await mcache.close()
    app.on_shutdown.append(mcache_shutdown)

    loader = jinja2.FileSystemLoader(options.http_server_template_dir)
    aiohttp_jinja2.setup(app,
                         loader=loader,
                         # enable_async=True,
                         context_processors=[current_user_ctx_processor],
                         )

    await setup_remotes(app, XForwardedRelaxed())
    setup_routes(app, options=options)

    if not options.verbose:
        setup_error_pages(app)

    if options.enable_aiohttp_debug_toolbar:
        aiohttp_debugtoolbar.setup(
            app, check_host=False, intercept_redirects=False)

# Put app as subapp under main_app and create an approbiate redirection
    main_app = web.Application()

    if parameters.cloud_identifier is None:
        parameters.cloud_identifier = secrets.token_urlsafe(12)

    async def main_app_handler(request):
        raise web.HTTPSeeOther(f'/{parameters.cloud_identifier}/')

    main_app.router.add_get('/', main_app_handler)
    main_app.add_subapp(f'/{parameters.cloud_identifier}/', app)

    logging.getLogger(__name__).info(f'Start {parameters.cloud_identifier}')
    return main_app


def _setup_access_log(options=None):
    formatter = logging.Formatter("%(message)s")
    Path(options.http_access_log_file).parent.mkdir(
        parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        options.http_access_log_file, mode='a',
        maxBytes=options.http_access_log_max_bytes,
        backupCount=options.http_access_log_backup_count,
        encoding=None, delay=0)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    access_log = logging.getLogger("aiohttp.access")
    access_log.setLevel(logging.DEBUG)
    access_log.addHandler(file_handler)
    return access_log


def _setup_logging(options=None):
    formatter = logging.Formatter(
        "%(asctime)s;%(levelname)s;%(name)s;%(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    if options.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    Path(options.log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(options.log_file, mode='a',
                                       maxBytes=options.log_max_bytes,
                                       backupCount=options.log_backup_count,
                                       encoding=None, delay=0)
    file_handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[stream_handler, file_handler])

    if options.enable_gmqtt_debug_log:
        logging.getLogger("gmqtt").setLevel(logging.DEBUG)
    else:
        logging.getLogger("gmqtt").setLevel(logging.ERROR)

    if options.enable_ssh_debug_log:
        logging.getLogger("asyncssh").setLevel(logging.DEBUG)
    else:
        logging.getLogger("asyncssh").setLevel(logging.ERROR)

    if options.enable_aiohttp_access_log:
        logging.getLogger("aiohttp.access").setLevel(logging.DEBUG)
    else:
        logging.getLogger("aiohttp.access").setLevel(logging.ERROR)


def _get_options():
    p = configargparse.ArgParser(
        default_config_files=['/etc/riego/conf.d/*.conf',
                              '~/.riego.conf',
                              PRIMARY_INI_FILE],
        args_for_writing_out_config_file=['-w',
                                          '--write-out-config-file'])
    p.add('-c', '--config', is_config_file=True, env_var='RIEGO_CONF',
          required=False, help='config file path')
# Database
    p.add('-d', '--db_filename', help='Path and name for DB file',
          default='db/riego.db')
    p.add('--db_migrations_dir',
          help='path to database migrations directory',
          default=pkg_resources.resource_filename('riego', 'migrations'))
# Logging
    p.add('-l', '--log_file', help='Full path to logfile',
          default='log/riego.log')
    p.add('--log_max_bytes', help='Maximum Evet Log Size in bytes',
          default=1024*300, type=int)
    p.add('--log_backup_count', help='How many files to rotate',
          default=3, type=int)
# Secrets & Scurity
    p.add('--max_age_remember_me', type=int, default=7776000)
    p.add('--cookie_name_remember_me', default="remember_me")
    p.add('--reset_admin', help='Reset admin-pw to given value an exit')
    p.add('--websockets_max_receive_size', type=int, default=1024)
    p.add('--ssh_key_algorithm', default='ssh-ed25519')
# Session keys
    p.add('--session_key_websocket_auth', default='websocket_auth')
    # TODO
    p.add('--session_key_user_id', default='user_id',
          help='# TODO not used Yet')
# HTTP-Server
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
    p.add('--http_access_log_file', help='Full path to access logfile',
          default='log/access.log')
    p.add('--http_access_log_max_bytes', help='Maximum file size in bytes',
          default=1024*300, type=int)
    p.add('--http_access_log_backup_count', help='How many files to rotate',
          default=3, type=int)
# Memcache
    p.add('--memcached_host', help='IP adress of memcached host',
          default='127.0.0.1')
    p.add('--memcached_port', help='Port of memcached service',
          default=11211, type=int)
# Cloud-Server
#    p.add('--cloud_identifier', help='Unique id for Cloud Identity')
    p.add('--cloud_api_url', help='Hostname for cloud service',
          default='https://cloud.finca-panorama.es/api_20210221/')
    p.add('--ssh_known_hosts', help='SSh-Server verification',
          default=pkg_resources.resource_filename('riego', 'ssh/known_hosts'))

# Directories
    p.add('--base_dir', help='Change only if you know what you are doing',
          default=Path(__file__).parent)
# MQTT
    p.add('-m', '--mqtt_host', help='IP adress of mqtt host',
          default='127.0.0.1')
    p.add('-p', '--mqtt_port', help='Port of mqtt service',
          default=1883, type=int)
    p.add('--mqtt_client_id', help='Client ID for MQTT-Connection',
          default=f'riego_ctrl_{socket.gethostname()}')

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

    p.add('--mqtt_cmnd_prefix', help='',
          default="cmnd")
    p.add('--mqtt_keyword_ON', help='',
          default="ON")
    p.add('--mqtt_keyword_OFF', help='',
          default="OFF")
# Parameter Default Values
    p.add('--parameters_smtp_hostname', default="smtp.gmail.com")
    p.add('--parameters_smtp_port', type=int, default=465)
    p.add('--parameters_smtp_security', default="use_tls=True")
    p.add('--parameters_smtp_user', default="user")
    p.add('--parameters_smtp_password', default="password")
    p.add('--parameters_smtp_from', default="riego@localhost")

    p.add('--parameters_start_time_1', default="19:00")
    p.add('--parameters_max_duartion', default="240")
# Debug
    p.add('--enable_aiohttp_debug_toolbar', action='store_true')
    p.add('--enable_aiohttp_access_log', action='store_true')
    p.add('--enable_asyncio_debug_log', action='store_true')
    p.add('--enable_ssh_debug_log', action='store_true')
    p.add('--enable_gmqtt_debug_log', action='store_true')
    p.add('--enable_timer_dev_mode', action='store_true')
    p.add('--WindowsSelectorEventLoopPolicy', action='store_true')

# Version, Help, Verbosity
    p.add('-v', '--verbose', help='verbose', action='store_true')
    p.add('--version', help='Print version and exit', action='store_true')
    p.add('--defaults', help='Print options with default values and exit',
          action='store_true')

    options = p.parse_args()
    if options.verbose:
        print(p.format_values())

    try:
        with open(PRIMARY_INI_FILE, 'xt') as f:
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

    if options.reset_admin:
        _reset_admin(options)
        exit(0)

    return options


def _reset_admin(options):
    from riego.db import setup_db
    import bcrypt

    db = setup_db(options=options)
    password = options.reset_admin

    if len(password) > 0:
        password = password.encode('utf-8')
        password = bcrypt.hashpw(password, bcrypt.gensalt(12))
        cursor = db.conn.cursor()
        cursor.execute('''UPDATE users
                        SET password = ?
                        WHERE id = ? ''', (password, 1))
        db.conn.commit()
        if cursor.rowcount == 1:
            print(f'Succesfully reset Admin PW: {password}')
        else:
            print('Unable to reset Admin PW:')
    db.conn.close()
