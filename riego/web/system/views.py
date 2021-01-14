import aiohttp_jinja2
from aiohttp.web_runner import GracefulExit
from aiohttp import web


import asyncio
import sys
import json


@aiohttp_jinja2.template('system/index.html')
async def system_index(request):
    #    return web.Response(text="Hello, world")
    return {'text': 'Hello, world2'}


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
    raise GracefulExit()


@aiohttp_jinja2.template('system/index.html')
async def system_setup(request):
    return {'text': 'Hello, world2'}


async def system_event_log(request):
    with open(request.app['options'].event_log, "rb") as fp:
        return web.Response(body=fp.read(), content_type="text/plain")


async def system_exc(request):
    raise NotImplementedError


async def _check_update(latest_version=None):
    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'pip', 'list', "-o", "--format=json",
        "--disable-pip-version-check", "--no-color", "--no-python-version-warning", 
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
        "--disable-pip-version-check", "--no-color", "--no-python-version-warning", "-q", "-q", "-q")
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
