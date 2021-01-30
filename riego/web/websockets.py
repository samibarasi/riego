from aiohttp import web
import json


class Websockets():
    def __init__(self, app):
        self._log = app['log']
        self._options = app['options']

        self._ws_list = []
        self._subscriptions = {}

        app.router.add_get(self._options.websocket_path, self._ws_handler)
        app.on_shutdown.append(self.shutdown)

    async def send_to_all(self, msg: dict) -> None:
        for ws in self._ws_list:
            await ws.send_str(msg)
        return None

    def subscribe(self, model: str, callback: callable) -> None:
        """Install a callback function for given model.

        :param model: name of data model that asks for websocket
        :type model: str
        :param callback: callback function that is called when data arrives
        :type callback: function with parameters msg
        :return: None
        :rtype: None
        """
        self._subscriptions[model] = callback
        return None

    async def _ws_handler(self, request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self._ws_list.append(ws)

    # Here possiblity to send init-message to Web-Client

        try:
            async for msg in ws:
                self._log.debug(msg)
                if msg.type == web.WSMsgType.TEXT:
                    msg = json.loads(msg.data)
                    await self._dispatch_message(msg)
                else:
                    break
        except Exception as e:
            self._log.error(f'websocket.py, exeption {e}')
        finally:
            self._log.debug(f'Finally ws remove: {ws}')
            self._ws_list.remove(ws)
        return ws

    async def _dispatch_message(self, msg: dict) -> bool:
        model = msg.get('model', None)
        if model is None:
            self._log.error(f'Message not for a data model: {msg}')
            return False
        callback_func = self._subscriptions.get(model, None)
        if callback_func is None:
            self._log.error(f'Message for an unknown data model: {msg}')
            return False
        try:
            await callback_func(msg)
        except Exception as e:
            self._log.error(
                f'websocket.py, exeption {e} in callable {callback_func}')
            return False
        return True

    async def shutdown(self, app) -> None:
        for ws in self._ws_list:
            self._log.debug(f'calling ws.close for: {ws}')
            await ws.close()
        return None
