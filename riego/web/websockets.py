from aiohttp import web
import json

__ws_list = None   # List of open websockets.
__subscriptions = {}
__log = None


def setup_websockets(app) -> list:
    global __ws_list
    global __log
    __log = app['log']
    if not isinstance(__ws_list, list):
        # very first run. We set up routes an install shutdown
        __ws_list = []
        app.router.add_get(app['options'].websocket_path,  _ws_handler)
        app.on_shutdown.append(_my_shutdown)
    return __ws_list


async def send_to_all(msg: dict) -> None:
    global __ws_list
    for ws in __ws_list:
        await ws.send_str(msg)
    return None


def subscribe(model: str, callback) -> None:
    """Install a callback function for given model.

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
    global __log
    global __ws_list
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    __ws_list.append(ws)

# Here possiblity to send init-message to Web-Client

    try:
        async for msg in ws:
            __log.debug(msg)
            if msg.type == web.WSMsgType.TEXT:
                msg = json.loads(msg.data)
                await dispatch_message(msg)
            else:
                break
    except Exception as e:
        __log.error(f'websocket.py, exeption {e}')
    finally:
        __log.debug(f'Finally ws remove: {ws}')
        __ws_list.remove(ws)
    return ws


async def dispatch_message(msg: dict) -> bool:
    global __subscriptions
    global __log
    model = msg.get('model', None)
    if model is None:
        __log.error(f'Message not for a data model: {msg}')
        return False
    callback_func = __subscriptions.get(model, None)
    if callback_func is None:
        __log.error(f'Message for an unknown data model: {msg}')
        return False
    try:
        await callback_func(msg)
    except Exception as e:
        __log.error(f'websocket.py, exeption {e} in callable {callback_func}')
        return False
    return True


async def _my_shutdown(app) -> None:
    global __ws_list
    for ws in __ws_list:
        __log.debug(f'calling ws.close for: {ws}')
        await ws.close()
    return None
