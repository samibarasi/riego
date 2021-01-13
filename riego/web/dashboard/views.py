from aiohttp import web
import aiohttp_jinja2


@aiohttp_jinja2.template('dashboard/index.html')
async def dashboard_index(request):
    #    return web.Response(text="Hello, world")
    return {'valves': request.app['valves'].get_dict()}


async def dashboard_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app['dashboard_ws'].add(ws)

    # await request.app['valves'].send_init_with_websocket()

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await request.app['valves'].websocket_handler(msg.data)
    finally:
        request.app['dashboard_ws'].discard(ws)

    return ws
