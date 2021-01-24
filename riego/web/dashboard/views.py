import aiohttp_jinja2


@aiohttp_jinja2.template('dashboard/index.html')
async def dashboard_index(request):
    return {'valves': request.app['valves'].get_dict_of_all()}
