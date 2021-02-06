import aiohttp_jinja2
from aiohttp_session import get_session
from riego.db import get_db


class Dashboard():
    def __init__(self, app):
        pass

    @aiohttp_jinja2.template('dashboard/index.html')
    async def index(self, request):
        session = await get_session(request)
        session['alert'] = {'class': 'alert-danger',
                            'heading': 'Danger!',
                            'text': 'lorem ipsum'}
        session.changed()

        c = get_db().conn.cursor()
        c.execute('SELECT * FROM valves')
        items = c.fetchall()
        get_db().conn.commit()

        return {'valves': items}
