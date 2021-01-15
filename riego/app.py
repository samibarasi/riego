import asyncio
import configargparse
import pkg_resources
import os
import pathlib
# import logging
# import sys

import riego.database
import riego.valves
import riego.parameter
import riego.mqtt
import riego.logger
import riego.timer

from riego.web.routes import setup_routes
from riego.web.middlewares import setup_middlewares
from riego.web.websockets import setup_websockets

from aiohttp import web
import jinja2
import aiohttp_jinja2
import aiohttp_debugtoolbar

from riego.__init__ import __version__


async def on_startup(app):
    app['log'].info("on_startup")
    app['background_timer'] = asyncio.create_task(app['timer'].start_async())
    app['background_mqtt'] = asyncio.create_task(app['mqtt'].start_async())


async def on_cleanup(app):
    app['log'].info("on_cleanup")
    app['background_timer'].cancel()
    await app['background_timer']
    app['background_mqtt'].cancel()
    await app['background_mqtt']


async def on_shutdown(app):
    app['log'].info("on_shutdown")


def main():
    p = configargparse.ArgParser(
        default_config_files=['/etc/riego/conf.d/*.conf', '~/.riego.conf'])
    p.add('-c', '--config', is_config_file=True, env_var='RIEGO_CONF',
          default='riego.conf', help='config file path')
    p.add('-d', '--database', help='Path and name for DB file',
          default='db/riego.db')
    p.add('-e', '--event_log', help='Full path and name for event logfile',
          default='log/event.log')
    p.add('--event_log_max_bytes', help='Maximum Evet Log Size in bytes',
          default=1024*300, type=int)
    p.add('--event_log_backup_count', help='How many files to rotate',
          default=3, type=int)
    p.add('-m', '--mqtt_host', help='IP adress of mqtt host',
          default='127.0.0.1')
    p.add('-p', '--mqtt_port', help='Port of mqtt service',
          default=1883, type=int)
    p.add('--mqtt_client_id', help='Client ID for MQTT-Connection',
          default='riego_controler')
    p.add('--database_migrations_dir',
          help='path to database migrations directory',
          default=pkg_resources.resource_filename('riego', 'migrations'))
    p.add('--base_dir', help='Change only if you know what you are doing',
          default=pathlib.Path(__file__).parent)
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
    p.add('-v', '--verbose', help='verbose', action='store_true')
    p.add('--version', help='Print version', action='store_true')
    p.add('--enable_aiohttp_debug_toolbar', action='store_true')
    p.add('--enable_asyncio_debug', action='store_true')
    p.add('--enable_timer_dev_mode', action='store_true')

    options = p.parse_args()

    if options.verbose:
        print(p.format_values())

    if options.version:
        print('Version: ', __version__)
        os.sys.exit()

    if options.enable_asyncio_debug:
        asyncio.get_event_loop().set_debug(True)

    if os.name == "posix":
        import uvloop  # pylint: disable=import-error
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    app = web.Application()

    app['options'] = options
    app['log'] = riego.logger.create_log(options)
    app['event_log'] = riego.logger.create_event_log(options)
    app['db'] = riego.database.Database(app)
    app['mqtt'] = riego.mqtt.Mqtt(app)
    app['valves'] = riego.valves.Valves(app)
    app['parameter'] = riego.parameter.Parameter(app)
    app['timer'] = riego.timer.Timer(app)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.on_shutdown.append(on_shutdown)

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(
        options.http_server_template_dir))

    setup_routes(app)
    setup_middlewares(app)
    setup_websockets(app)

    if options.enable_aiohttp_debug_toolbar:
        aiohttp_debugtoolbar.setup(app, check_host=False)

    app['log'].info("Start")
    app['event_log'].info('Start')

    web.run_app(app,
                host=options.http_server_bind_address,
                port=options.http_server_bind_port)
    print("Exit")
