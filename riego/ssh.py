import asyncssh
import asyncio
import aiohttp
import json
from pathlib import Path


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
                                username='sddwdfwdwe',
                                client_keys=['ssh/ssh_user_key'],
#                                client_certs=['ssh/id_rsa-cert.pub'],
                                known_hosts='riego/ssh/known_hosts') as conn:
        result = await conn.run('ls abc', check=True)
        print(result.stdout, end='')


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
