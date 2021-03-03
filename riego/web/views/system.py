import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from riego.model.parameters import get_parameters
from riego.web.security import raise_permission
from riego.cloud import get_cloud

import asyncio
import sys
import json
import secrets

from riego.__init__ import __version__
from pkg_resources import packaging

router = web.RouteTableDef()


def setup_routes_system(app):
    app.add_routes(router)


@router.get("/system", name='system')
@aiohttp_jinja2.template('system/index.html')
async def system_index(request):
    await raise_permission(request, permission=None)
    text = ''
    installed_version = await _check_installed()
    if not packaging.version.parse(installed_version) == packaging.version.parse(__version__):  # noqa: E501
        text = '''Diese Riego Instanz läuft in der Version {}
                und entspricht nicht der installierten Version {}.'''  # noqa: E501
        text = text.format(__version__, installed_version)

    return {"text": text}


@router.get("/system/cloud", name='system_cloud')
@aiohttp_jinja2.template('system/index.html')
async def system_check_cloud(request):
    await raise_permission(request, permission=None)
    cloud = get_cloud()
    cloud_url = await cloud.check_cloud()
    return {'cloud_url': cloud_url}


@router.post("/system/cloud")
@aiohttp_jinja2.template('system/index.html')
async def system_create_cloud(request):
    await raise_permission(request, permission=None)
    csrf_token = secrets.token_urlsafe()
    session = await get_session(request)
    session['csrf_token'] = csrf_token
    cloud = get_cloud()
    if await cloud.create_cloud():
        raise web.HTTPSeeOther(
            request.app.router['system_cloud'].url_for())
    text = "Failed to create cloud connection"
    return {'text':  text}


@router.get("/system/check_update", name='system_check_update')
@aiohttp_jinja2.template('system/index.html')
async def system_check_update(request):
    await raise_permission(request, permission=None)
    update = await _check_update("No update")
    return {'text':  update}


@router.get("/system/do_update", name='system_do_update')
@aiohttp_jinja2.template('system/index.html')
async def system_do_update(request):
    await raise_permission(request, permission=None)
    await _do_update()
    return {'text': "Restart erforderlich"}


@router.get("/system/restart", name='system_restart')
@aiohttp_jinja2.template('system/index.html')
async def system_restart(request):
    await raise_permission(request, permission=None)
    # TODO shedule exit for a few seconds and return a redirect
    asyncio.get_event_loop().call_later(1, exit, 0)
    raise web.HTTPSeeOther(request.app.router['system'].url_for())


@router.get("/system/log_file", name='system_log_file')
@aiohttp_jinja2.template('system/index.html')
async def system_log_file(request):
    await raise_permission(request, permission=None)
    with open(request.app['options'].log_file, "rt") as fp:
        return web.Response(body=fp.read(), content_type="text/plain")
        # return {'text': fp.read()}


@router.get("/system/parameters", name='system_parameters')
@aiohttp_jinja2.template("system/parameters.html")
async def parameters(request: web.Request):
    await raise_permission(request, permission=None)
    items = {}
    items['max_duration'] = get_parameters().max_duration
    items['start_time_1'] = get_parameters().start_time_1
    items['smtp_hostname'] = get_parameters().smtp_hostname
    items['smtp_port'] = get_parameters().smtp_port
    items['smtp_security'] = get_parameters().smtp_security
    items['smtp_user'] = get_parameters().smtp_user
    items['smtp_password'] = get_parameters().smtp_password
    items['smtp_from'] = get_parameters().smtp_from

    return {"items": items}


@router.post("/system/parameters")
@aiohttp_jinja2.template("system/parameters.html")
async def parameters_apply(request: web.Request):
    await raise_permission(request, permission=None)
    parameters = get_parameters()
    items = await request.post()
    for item in items:
        if getattr(parameters, item, None) is not None:
            setattr(parameters, item, items[item])
    return {"items": items}


async def _check_installed():
    version = "0.0.0"
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
    exit(0)
    # return proc.returncode
