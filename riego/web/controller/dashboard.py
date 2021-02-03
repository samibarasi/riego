import aiohttp_jinja2
from aiohttp_session import get_session

from riego.model.valves import Valve


@aiohttp_jinja2.template('dashboard/index.html')
async def dashboard_index(request):
    session = await get_session(request)
    session['alert'] = {'class': 'alert-danger',
                        'heading': 'Danger!',
                        'text': 'lorem ipsum'}
    session.changed()
    session = request.app['db'].Session()
    items = session.query(Valve).all()
    session.close()
    return {'valves': items}
