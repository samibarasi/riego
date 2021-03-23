from aiohttp import web
import json
import asyncio
import bcrypt

from logging import getLogger
_log = getLogger(__name__)


_instance = None


def get_websockets():
    global _instance
    return _instance


def setup_websockets(app=None, db=None, options=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Websockets(app=app, db=db, options=options)
    return _instance


class Websockets():
    def __init__(self, app=None, db=None, options=None):
        global _instance
        if _instance is None:
            _instance = self

        self._options = options
        self._db = db

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
        """Install a callback function for given scope.

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
        max_msg_size = self._options.websockets_max_receive_size
        ws = web.WebSocketResponse(max_msg_size=max_msg_size)
        await ws.prepare(request)

        self._ws_list.append(ws)

        try:
            async for msg in ws:
                _log.debug(msg)
                if msg.type == web.WSMsgType.TEXT:
                    await self._dispatch_message(msg.data)
                else:
                    _log.error(f'Unknown message type: {msg}')
                    await asyncio.sleep(3)
                    break
        except Exception as e:
            _log.error(f'Exeption while reading from websocket: {e}')
            await asyncio.sleep(3)
        finally:
            _log.debug(f'Removing closed websocket: {ws}')
            self._ws_list.remove(ws)
        return ws

    async def _dispatch_message(self, msg: dict) -> bool:
        msg = json.loads(msg)
        scope = msg.get('scope', '')
        if scope == "authenticate_v1":
            # TODO Implemet a one-time authentication
            return True

        if len(scope) == 0:
            _log.error(f'Message not for a scope: {msg}')
            await asyncio.sleep(3)
            return False

        token = msg.get('token', '')
        sequence = msg.get('sequence', '')

        if len(sequence) == 0 or len(token) == 0:
            _log.error(f"Websocket-Auth: missing var {sequence},{token}")
            await asyncio.sleep(3)
            return False

        cursor = self._db.conn.cursor()
        cursor.execute('''SELECT * FROM users_tokens
                    WHERE sequence = ?''', (sequence,))
        item = cursor.fetchone()
        if item is None:
            _log.error(f"Websocket-Auth: unknown {sequence},{token}")
            await asyncio.sleep(3)
            return False

        token = token.encode('utf-8')
        if bcrypt.checkpw(token, item['hash']):
            _log.debug(f'authenticate: {token}, sequence: {sequence}')
        else:
            _log.error(f'no authenticate: {token}, sequence: {sequence}')
            await asyncio.sleep(3)
            return False

        callback_func = self._subscriptions.get(scope, None)
        if callback_func is None:
            _log.error(f'Message for an unknown scope: {msg}')
            await asyncio.sleep(3)
            return False
        try:
            await callback_func(msg)
        except Exception as e:
            _log.error(f'Exeption in {callback_func}: {e}')
            await asyncio.sleep(3)
            return False
        return True

    async def shutdown(self, app) -> None:
        loop = asyncio.get_event_loop()
        for ws in self._ws_list:
            _log.debug(f'calling ws.close for: {ws}')
            loop.create_task(ws.close())
        return None
