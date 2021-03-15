import asyncssh
import asyncio
import aiohttp
from aiohttp import ClientError


from logging import getLogger
_log = getLogger(__name__)

_instance = None


def get_cloud():
    global _instance
    return _instance


def setup_cloud(app=None, options=None, parameters=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Cloud(app=app, options=options, parameters=parameters)
    return _instance


class Cloud:
    def __init__(self, app=None, options=None, parameters=None):
        global _instance
        if _instance is None:
            _instance = self

        self._parameters = parameters
        self._options = options
        self._STOP = False
        self._conn = None
        self._listener = None
        app.cleanup_ctx.append(self._ssh_engine)

    async def _ssh_engine(self, app):
        task = asyncio.create_task(self._startup(app))
        yield
        await self._shutdown(app, task)

    async def _startup(self, app) -> None:
        _log.debug('Ssh Engine startup called')

# TODO move the following code to Web-Interface

        while not self._STOP:
            if (self._parameters.ssh_server_hostname is None or
                self._parameters.ssh_server_port is None or
                self._parameters.ssh_server_listen_port is None or
                self._parameters.cloud_server_url is None or
                    self._parameters.ssh_user_key is None):
                await asyncio.sleep(3)
                continue
            ssh_user_key = asyncssh.import_private_key(
                self._parameters.ssh_user_key)
            try:
                async with asyncssh.connect(
                        self._parameters.ssh_server_hostname,
                        port=self._parameters.ssh_server_port,
                        username=self._parameters.cloud_identifier,
                        client_keys=ssh_user_key,
                        known_hosts=self._options.ssh_known_hosts,
                        keepalive_interval=60
                ) as self._conn:
                    self._listener = await self._conn.forward_remote_port(
                        'localhost',  # Bind to localhost on remote Server
                        self._parameters.ssh_server_listen_port,
                        'localhost',
                        self._options.http_server_bind_port
                    )
                    _log.debug('remote 127.0.0.1:{}, local 127.0.0.1:{}'.format(  # noqa: E501
                        self._parameters.ssh_server_listen_port,
                        self._options.http_server_bind_port))
                    await self._listener.wait_closed()
            except Exception as e:
                _log.debug(f'SSH-Exception: {e}')
            await asyncio.sleep(10)

    async def _shutdown(self, app, task) -> None:
        _log.debug('Ssh Engine shutdown called')
        self._STOP = True
        if self._listener is not None:
            self._listener.close()
        if self._conn is not None:
            self._conn.close()
#            await self._conn.wait_closed()
        return None

    async def create_cloud(self):
        key = asyncssh.generate_private_key(self._options.ssh_key_algorithm)
        self._parameters.ssh_user_key = key.export_private_key()
        public_user_key = key.export_public_key().decode('ascii')

        data = {'cloud_identifier': self._parameters.cloud_identifier,
                'public_user_key': public_user_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self._options.cloud_api_url,
                                        json=data) as resp:
                    if resp.status != 200:
                        return
                    data = await resp.json()
        except ClientError as e:
            _log.debug(f'Unable to access remote api: {e}')
            return False
        else:
            self._parameters.ssh_server_hostname = data['ssh_server_hostname']  # noqa: E501
            self._parameters.ssh_server_port = data['ssh_server_port']
            self._parameters.ssh_server_listen_port = data['ssh_server_listen_port']  # noqa: E501
            self._parameters.cloud_server_url = data['cloud_server_url']  # noqa: E501
            return True

    async def check_cloud(self):
        if (
            self._parameters.ssh_server_hostname is None or
            self._parameters.ssh_server_port is None or
            self._parameters.ssh_server_listen_port is None or
            self._parameters.ssh_user_key is None or
            self._parameters.cloud_server_url is None
        ):
            return None
        else:
            url = '{}/{}/'.format(
                       self._parameters.cloud_server_url,
                       self._parameters.cloud_identifier)
            return url
