import asyncssh
import asyncio
import aiohttp
import json
from pathlib import Path


from logging import getLogger
_log = getLogger(__name__)

_instance = None


def get_ssh():
    global _instance
    return _instance


def setup_ssh(app=None, options=None, parameters=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Ssh(app=app, options=options, parameters=parameters)
    return _instance


class Ssh:
    def __init__(self, app=None, options=None, parameters=None):
        global _instance
        if _instance is None:
            _instance = self

        self._task = None
        self._conn = None
        app.cleanup_ctx.append(self._ssh_engine)

    async def _ssh_engine(self, app):
        task = asyncio.create_task(self._startup(app))
        yield
        # TODO _shutdown should not be an awaitable
        await self._shutdown(app, task)

    async def _startup(self, app) -> None:
        _log.debug('Ssh Engine startup called')
        async with asyncssh.connect('127.0.0.1',
                                    port=8022,
                                    username='tt4',
                                    client_keys=['ssh/ssh_user_key'],
                                    known_hosts='riego/ssh/known_hosts') as conn:
            
            listener = await conn.forward_remote_port('localhost', 3334, 'localhost', 8080)
            await listener.wait_closed()

    async def _shutdown(self, app, task) -> None:
        _log.debug('Ssh Engine shutdown called')
        await task.cancelled()
        return None


async def store_new_keys(options=None):

    Path(options.ssh_user_key).parent.mkdir(parents=True, exist_ok=True)

    user_key = asyncssh.generate_private_key(options.ssh_key_algorithm)
    user_key.write_private_key(options.ssh_user_key)
    user_key.write_public_key(f'{options.ssh_user_key}.pub')

    public_user_key = user_key.export_public_key().decode('ascii')

    print(public_user_key)
    data = {'cloud_identifier': options.cloud_identifier,
            'public_user_key': public_user_key}

    async with aiohttp.ClientSession() as session:
        async with session.post(options.cloud_api_url, json=data) as resp:
            print(resp.status)
            data = await resp.json()

    user_cert = asyncssh.import_certificate(data['user_cert'])
    user_cert.write_certificate(f'{options.ssh_user_key}-cert.pub')
    print(data['public_user_key'])
    print(data['user_cert'])


async def ssh_connect(options=None):
    async with asyncssh.connect('127.0.0.1',
                                port=8022,
                                username='tt4',
                                client_keys=['ssh/ssh_user_key'],
                                #                                client_certs=['ssh/id_rsa-cert.pub'],
                                known_hosts='riego/ssh/known_hosts') as conn:
        listener = await conn.forward_remote_port('localhost', 3334, 'localhost', 8080)
#        result = await conn.run('ls abc', check=True)
#        print(result.stdout, end='')
        await listener.wait_closed()


async def main(options=None):
    await ssh_connect(options=options)

#    await store_new_keys(options=options)


if __name__ == "__main__":

    class Options():
        def __init__(self):
            self.ssh_user_key = "ssh/ssh_user_key"
            self.cloud_identifier = "dfsgdfgdfsgsdfg"
            self.cloud_api_url = 'http://127.0.0.1:8181/api_20210221/'
            self.ssh_key_algorithm = 'ssh-ed25519'

    options = Options()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(options=options))
