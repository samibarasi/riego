import asyncio
import sys
import json


async def run():

    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'pip', 'list', "-o", "--format=json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        data = json.loads(stdout)
        for item in data:
            print(item['name'])

# asyncio.run(run())

print ("Test{}string{}".format(1,3))
