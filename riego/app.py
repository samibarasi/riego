import asyncio
import configargparse
import pkg_resources
import os
import pathlib
import weakref
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

from aiohttp import web
import jinja2
import aiohttp_jinja2
import aiohttp_debugtoolbar

from riego.__init__ import __version__


async def start_background_tasks(app):
    app['background_timer'] = asyncio.create_task(app['timer'].start_async())
    app['background_mqtt'] = asyncio.create_task(app['mqtt'].start_async())


async def cleanup_background_tasks(app):
    app['background_timer'].cancel()
    await app['background_timer']
    app['background_mqtt'].cancel()
    await app['background_mqtt']


async def shutdown_websockets(app):
    for ws in app["dashboard_ws"]:
        await ws.close()


# os.path.join(os.path.dirname(__file__), "websocket.html")

def main():
    p = configargparse.ArgParser(
        default_config_files=['/etc/riego/conf.d/*.conf', '~/.riego.conf'])
    p.add('-c', '--config', is_config_file=True, env_var='RIEGO_CONF',
          default='riego.conf', help='config file path')
    p.add('-d', '--database', help='path to DB file', default='db/riego.db')
    p.add('-e', '--event_log', help='path to event logfile',
          default='log/event.log')
    p.add('-m', '--mqtt_host', help='IP adress of mqtt host', required=True)
    p.add('-p', '--mqtt_port', help='Port of mqtt service', required=True,
          type=int)
    p.add('--database_migrations_dir',
          help='path to database migrations directory',
          default=pkg_resources.resource_filename('riego', 'migrations'))
    p.add('--base_dir', help='Change only if you know what you are doing',
          default=pathlib.Path(__file__).parent)
    p.add('--http_server_bind_address',
          help='http-server bind address', default='localhost')
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
    app['dashboard_ws'] = weakref.WeakSet()

    app['options'] = options
    app['log'] = riego.logger.create_log(options)
    app['event_log'] = riego.logger.create_event_log(options)
    app['db'] = riego.database.Database(app)
    app['mqtt'] = riego.mqtt.Mqtt(app)
    app['valves'] = riego.valves.Valves(app)
    app['parameter'] = riego.parameter.Parameter(app)
    app['timer'] = riego.timer.Timer(app)

    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    app.on_shutdown.append(shutdown_websockets)

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(
        options.http_server_template_dir))

    setup_routes(app)
    setup_middlewares(app)

    if options.enable_aiohttp_debug_toolbar:
        aiohttp_debugtoolbar.setup(app, check_host=False)

    app['log'].info("Start")
    app['event_log'].info('Start')

    web.run_app(app,
                host=options.http_server_bind_address,
                port=options.http_server_bind_port)
