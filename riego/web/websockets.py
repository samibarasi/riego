from aiohttp import web
import json

__ws_list = None   # List of open websockets.
__subscriptions = {}


def setup_websockets(app) -> list:
    global __ws_list
    if not isinstance(__ws_list, list):
        # very first run. We set up routes an install shutdown
        __ws_list = []
        app.router.add_get(app['options'].websocket_path,  _ws_handler)
        app.on_shutdown.append(_my_shutdown)
    return __ws_list


async def send_to_all(msg: dict) -> None:
    for ws in __ws_list:
        await ws.send_str(msg)
    return None


def subscribe(model: str, callback) -> None:
    """Install a callback function for given model. 

    Blödsinn: Eacch message
    should contain a json data like this: {model: <model_name>}

    :param model: name of data model that asks for websocket
    :type model: str
    :param callback: callback function that is called when data arrives
    :type callback: function with parameter msg
    :return: None
    :rtype: None
    """
    global __subscriptions
    __subscriptions[model] = callback
    return None


async def _ws_handler(request) -> web.WebSocketResponse:
    global __subscriptions
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    __ws_list.append(ws)

# Here possiblity to send init-message to Web-Client

    try:
        async for msg in ws:
            print(msg)
            if msg.type == web.WSMsgType.TEXT:
                msg = json.loads(msg.data)
                await dispatch_message(msg)
    finally:
        print(f'Finally ws remove: {ws}')
        __ws_list.remove(ws)
    return ws


async def dispatch_message(msg: dict) -> bool:
    global __subscriptions
    model = msg.get('model', None)
    if model is None:
        print(f'Message not for a data model: {msg}')
        return False
    callback_func = __subscriptions.get(model, None)
    if callback_func is None:
        print(f'Message for an unknown data model: {msg}')
        return False
    try:
        await callback_func(msg)
    except Exception as e:
        print(f'websocket.py, exeption {e} in callable {callback_func}')
        return False
    return True

async def _my_shutdown(app) -> None:
    for ws in __ws_list:
        await ws.close()
    return None
