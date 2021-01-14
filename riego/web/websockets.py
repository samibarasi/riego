from aiohttp import web
import json


__ws_list = None
__subscriptions = {}


def setup_websockets(app):
    global __ws_list
    if not isinstance(__ws_list, list):
        __ws_list = []
        app.router.add_get('/ws', _ws_handler)
        app.on_shutdown.append(_my_shutdown)
    return __ws_list


async def send_to_all(msg: dict):
    for ws in __ws_list:
        await ws.send_str(msg)
    return None


def subscribe(model: str, callback):
    global __subscriptions
    __subscriptions[model] = callback
    return None


async def _ws_handler(request):
    global __subscriptions
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    __ws_list.append(ws)

# Here possiblity to send init-message to Web-Client

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                msg = json.loads(msg.data)
                # Callback function from data Model (yet only 'valves')
                func = __subscriptions.get(msg['model'], lambda x: None)
                await func(msg)

    finally:
        __ws_list.remove(ws)
    return ws


async def _my_shutdown(app):
    for ws in __ws_list:
        await ws.close()
    return None
