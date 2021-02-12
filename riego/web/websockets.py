from aiohttp import web
import json
import asyncio
from logging import getLogger
_log = getLogger(__name__)


_instance = None


def get_websockets():
    global _instance
    return _instance


def setup_websockets(app=None, options=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Websockets(app=app, options=options)
    return _instance


class Websockets():
    def __init__(self, app=None, options=None):
        global _instance
        if _instance is None:
            _instance = self

        self._options = options

        self._ws_list = []
        self._subscriptions = {}

        app.router.add_get(self._options.websocket_path,
                           self._ws_handler,
                           name='websockets')
        app.on_shutdown.append(self.shutdown)

    async def send_to_all(self, msg: dict) -> None:
        for ws in self._ws_list:
            await ws.send_str(msg)
        return None

    def subscribe(self, scope: str, callback: callable) -> None:
        """Install a callback function for given model.

        :param scope: name of scope that asks for websocket
        :type scope: str
        :param callback: callback function that is called when data arrives
        :type callback: function with parameters msg
        :return: None
        :rtype: None
        """
        self._subscriptions[scope] = callback
        return None

    async def _ws_handler(self, request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self._ws_list.append(ws)

    # Here possiblity to send init-message to Web-Client

        try:
            async for msg in ws:
                _log.debug(msg)
                if msg.type == web.WSMsgType.TEXT:
                    msg = json.loads(msg.data)
                    await self._dispatch_message(msg)
                else:
                    break
        except Exception as e:
            _log.error(f'websocket.py, exeption {e}')
        finally:
            _log.debug(f'Finally ws remove: {ws}')
            self._ws_list.remove(ws)
        return ws

    async def _dispatch_message(self, msg: dict) -> bool:
        model = msg.get('scope', None)
        if model is None:
            _log.error(f'Message not for a scope: {msg}')
            return False
        callback_func = self._subscriptions.get(model, None)
        if callback_func is None:
            _log.error(f'Message for an unknown scope: {msg}')
            return False
        try:
            await callback_func(msg)
        except Exception as e:
            _log.error(
                f'websocket.py, exeption {e} in callable {callback_func}')
            return False
        return True

    async def shutdown(self, app) -> None:
        loop = asyncio.get_event_loop()
        for ws in self._ws_list:
            _log.debug(f'calling ws.close for: {ws}')
            loop.create_task(ws.close())
        return None
