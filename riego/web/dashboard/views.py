import aiohttp_jinja2
from aiohttp_session import get_session


@aiohttp_jinja2.template('dashboard/index.html')
async def dashboard_index(request):
    session = await get_session(request)
    session['alert'] = {'class': 'alert-danger',
                        'heading': 'Danger!',
                        'text': 'lorem ipsum'}
    session.changed()
    return {'valves': request.app['valves'].get_dict_of_all()}
