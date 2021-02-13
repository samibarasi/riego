import aiomcache
from aiohttp_session import setup as session_setup, get_session
from aiohttp_session.memcached_storage import MemcachedStorage

# for testing
import time
from aiohttp import web

from logging import getLogger
_log = getLogger(__name__)

_instance = None


def _get_http_sessions():
    global _instance
    return _instance


def setup_http_sessions(app=None, options=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Http_sessions(app=app, options=options)
    return _instance


class Http_sessions:
    def __init__(self, app=None, options=None):
        global _instance
        if _instance is None:
            _instance = self

        self._mcache_client = aiomcache.Client(
            options.memcached_host, options.memcached_port)
        session_setup(app, MemcachedStorage(self._mcache_client))

        app.on_shutdown.append(self._on_shutdown)
        app.router.add_get('/session_test', self.__session_test)

    async def _on_shutdown(self, app):
        await self._mcache_client.close()

    async def __session_test(self, request):
        session = await get_session(request)
        last_visit = session['last_visit'] if 'last_visit' in session else None
        session['last_visit'] = time.time()
        text = 'Last visited: {}'.format(last_visit)
        return web.Response(text=text)
