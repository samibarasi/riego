import aiohttp_jinja2
from riego.db import get_db
from riego.web.security import raise_permission

from logging import getLogger
_log = getLogger(__name__)

@aiohttp_jinja2.template('dashboard/index.html')
async def index(self, request):
    await raise_permission(request, permission=None)

    cursor = get_db().conn.cursor()
    cursor.execute("""SELECT *, date(last_run) AS date_last_run
                FROM valves
                WHERE is_hidden = 0""")
    items = cursor.fetchall()
    get_db().conn.commit()

    return {'valves': items}
