import aiohttp_jinja2
from aiohttp import web


import asyncio
import sys
import json

from riego.__init__ import __version__
from pkg_resources import packaging


@aiohttp_jinja2.template('system/index.html')
async def system_index(request):
    text = ''
    installed_version = await _check_installed()
    if not packaging.version.parse(installed_version) == packaging.version.parse(__version__):  # noqa: E501
        text = 'Diese Riego Instanz läuft in der Version {} und entspricht nicht der installierten Version {}.'  # noqa: E501
        text = text.format(__version__, installed_version)

    #    return web.Response(text="Hello, world")
    return {'text': text}


@aiohttp_jinja2.template('system/index.html')
async def system_check_update(request):
    update = await _check_update("No update")
    return {'text':  update}


@aiohttp_jinja2.template('system/index.html')
async def system_do_update(request):
    await _do_update()
    return {'text': "Restart erforderlich"}


@aiohttp_jinja2.template('system/index.html')
async def system_restart(request):
    exit(0)


@aiohttp_jinja2.template('system/index.html')
async def system_setup(request):
    return {'text': 'Hello, world2'}


@aiohttp_jinja2.template('system/index.html')
async def system_event_log(request):
    with open(request.app['options'].event_log, "rt") as fp:
        # return web.Response(body=fp.read(), content_type="text/plain")
        return {'text': fp.read()}


async def system_exc(request):
    raise NotImplementedError


async def _check_installed(version=None):
    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'pip', 'list', "--format=json",
        "--disable-pip-version-check",
        "--no-color",
        "--no-python-version-warning",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    data = json.loads(stdout)
    for item in data:
        if item['name'] == 'riego':
            version = item['version']
            break
    return version


async def _check_update(latest_version=None):
    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'pip', 'list', "-o", "--format=json",
        "--disable-pip-version-check",
        "--no-color",
        "--no-python-version-warning",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    data = json.loads(stdout)
    for item in data:
        if item['name'] == 'riego':
            latest_version = item['latest_version']
            break
    return latest_version


async def _do_update():
    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'pip', 'install', "riego", "--upgrade",
        "--disable-pip-version-check",
        "--no-color",
        "--no-python-version-warning",
        "-q", "-q", "-q")
    await proc.wait()
    return proc.returncode


async def _stream_rsponse(request: web.Request) -> web.StreamResponse:
    resp = web.StreamResponse()
    name = request.match_info.get("name", "Anonymous")
    answer = ("Hello, " + name).encode("utf8")
    resp.content_length = len(answer)
    resp.content_type = "text/plain"
    await resp.prepare(request)
    await resp.write(answer)
    await resp.write_eof()
    return resp
