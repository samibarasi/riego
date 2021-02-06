from datetime import datetime, timedelta
import asyncio
from sqlite3 import IntegrityError
import logging


_log = logging.getLogger(__name__)

_instance = None


def get_timer():
    global _instance
    return _instance


def setup_timer(app=None, options=None, db=None, mqtt=None, valves=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Timer(app=app, options=options, db=db,
                      mqtt=mqtt, valves=valves)
    return _instance


class Timer():
    def __init__(self, app=None, options=None,
                 db=None, mqtt=None, valves=None):
        self._options = options
        self._db_conn = db.conn
        self._mqtt = mqtt
        self._valves = valves

        self._running_period_end = None
        self._running_period_start = None

        self._stop = False
        self._task = None

        self._current_valve_running = None

        app.cleanup_ctx.append(self.timer_engine)

    async def timer_engine(self, app):
        self._task = asyncio.create_task(self._timer_loop())
        yield
        self._shutdown(self._task)

    async def _timer_loop(self) -> None:
        _log.debug('Timer Engine started')
        while not self._stop:
            await asyncio.sleep(3)
            await self._check_updates()
            c = self._db_conn.cursor()
            c.execute("""SELECT * FROM valves ORDER BY valves.prio""")
            valves = c.fetchall()
            self._db_conn.commit()
            for valve in valves:
                await self._dispatch_valve(valve)
            print(f'cur_valve_run: {self._current_valve_running}')
        if valve is not None:
            await self._valves.set_off_try(valve['id'])
        return None

    async def _check_updates(self):
        return None

    async def _dispatch_valve(self, valve):
        print(valve['name'])
        if not self._mqtt.client.is_connected:
            return None
        if valve is None:
            return None
        if valve['is_running'] == 1:
            self._current_valve_running = valve['id']
            if await self._check_to_switch_off(valve):
                self._current_valve_running = 0
                return 0
            else:
                self._current_valve_running = valve['id']
                return 1
        if valve['is_hidden']:
            return None
        if not valve['is_enabled']:
            return None
        if valve['is_running'] == -1:
            return None
        if valve['is_running'] == 0:
            if (not self._current_valve_running and
                    await self._check_to_switch_on(valve)):
                self._current_valve_running = valve['id']
                return 1
        return None

    async def _check_to_switch_off(self, valve) -> bool:
        ret = False
        print("check off id: {}".format(valve['id']))
        if self._options.enable_timer_dev_mode:
            td = timedelta(minutes=0, seconds=valve['duration'])
        else:
            td = timedelta(minutes=valve['duration'])

        if datetime.now() - valve['last_shedule'] > td:
            # Laufzeit erreicht
            await self._valves.set_off_try(valve['id'])
            _log.debug('valveOff: {}'.format(valve['name']))
            ret = True
        return ret

    async def _check_to_switch_on(self, valve) -> bool:
        ret = False
        print("check on id: {}".format(valve['id']))
        if self._options.enable_timer_dev_mode:
            td = timedelta(days=0, seconds=valve['interval'])
        else:
            td = timedelta(days=valve['interval'])

        if (datetime.now() - valve['last_shedule'] > td and
                await self._is_running_period()):
            # Intervall erreicht
            await self._valves.set_on_try(valve['id'])
            try:
                with self._db_conn:
                    self._db_conn.execute(
                        """UPDATE valves SET last_shedule = ? WHERE id = ? """,
                        (datetime.now(), valve['id']))
            except IntegrityError as e:
                pass
                _log.error(f'update for last_shedule failed: {e}')
                return False
            _log.debug('valveOn: {}'.format(valve['name']))
        return ret

    def _shutdown(self, task) -> None:
        _log.debug('Timer Engine shutdown called')
        self._stop = True

    async def _is_running_period(self) -> bool:
        c = self._db_conn.cursor()
        c.execute("""SELECT * FROM parameters WHERE key = ?""",
                  ('max_duration',))
        max_duration = c.fetchone()['value']
        c.execute("""SELECT * FROM parameters WHERE key = ?""",
                  ('start_time_1',))
        start_time_1 = c.fetchone()['value']
        self._db_conn.commit()

        start_hour, start_minute = start_time_1.split(':')

        if self._running_period_start is None:
            self._running_period_start = datetime.now().replace(
                hour=int(start_hour), minute=int(start_minute), second=0)

        if datetime.now() < self._running_period_start:
            self._running_period_end = None
            return False

        if self._running_period_end is None:
            self._running_period_end = self._running_period_start + \
                timedelta(minutes=int(max_duration))

        if datetime.now() > self._running_period_end:
            self._running_period_start = None
            return False
        return True
