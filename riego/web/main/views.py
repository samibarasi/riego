import aiohttp_jinja2


@aiohttp_jinja2.template('main/index.html')
async def main_index(request):
    #    return web.Response(text="Hello, world")
    return {'text': 'Hello, world2'}


@aiohttp_jinja2.template('main/index.html')
async def main_system(request):
    #    return web.Response(text="Hello, world")
    exit(0)
    return {'text': 'Hello, world2'}


async def exception_handler(request):
    raise NotImplementedError
