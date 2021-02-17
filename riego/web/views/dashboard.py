import aiohttp_jinja2
from riego.db import get_db
from riego.web.security import raise_permission


class Dashboard():
    def __init__(self, app):
        self._db_conn = get_db().conn

    @aiohttp_jinja2.template('dashboard/index.html')
    async def index(self, request):
        await raise_permission(request, permission=None)

        cursor = self._db_conn.cursor()
        cursor.execute("""SELECT *, date(last_run) AS date_last_run
                    FROM valves
                    WHERE is_hidden = 0""")
        items = cursor.fetchall()
        self._db_conn.commit()

        return {'valves': items}
