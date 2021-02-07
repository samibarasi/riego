from datetime import datetime, timedelta
import asyncio
from sqlite3 import IntegrityError
import logging


_log = logging.getLogger(__name__)

_instance = None


def get_timer():
    global _instance
    return _instance


def setup_timer(app=None, options=None,
                db=None, mqtt=None,
                parameters=None, valves=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Timer(app=app, options=options,
                      db=db, mqtt=mqtt,
                      parameters=parameters, valves=valves)
    return _instance


class Timer():
    def __init__(self, app=None, options=None,
                 db=None, mqtt=None,
                 parameters=None, valves=None):
        self._options = options
        self._db_conn = db.conn
        self._mqtt = mqtt
        self._parameters = parameters
        self._valves = valves

        self._running_period_end = None
        self._running_period_start = None

        self._stop = False
        self._task = None

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
            c.execute("""SELECT MAX(valves.is_running) AS one_is_on, valves.*
                        FROM valves
                        ORDER BY valves.prio""")
            valves = c.fetchall()
            self._db_conn.commit()
            for valve in valves:
                await self._dispatch_valve(valve)
        # Close last valve on exit
        if valve is not None:
            await self._valves.set_off_try(valve['id'])
        return None

    async def _check_updates(self):
        return None

    async def _dispatch_valve(self, valve):
        # _log.debug("dispatch_valve: {}".format(valve['name']))
        if not self._mqtt.client.is_connected:
            return None
        if valve is None:
            return None
        if valve['is_running'] == 1:
            await self._check_to_switch_off(valve)
            return None
        if valve['is_hidden']:
            return None
        if not valve['is_enabled']:
            return None
        if valve['is_running'] == -1:
            return None
        if valve['is_running'] == 0 and not valve['one_is_on'] == 1:
            await self._check_to_switch_on(valve)
            # TODO Waiting Timeout period
            await asyncio.sleep(1)
            return None
        return None

    async def _check_to_switch_off(self, valve) -> bool:
        ret = False
        print("check_to_switch_off for id: {}".format(valve['id']))
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
        _log.debug("check_to_switch_on for id: {}".format(valve['id']))
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
        max_duration = self._parameters.max_duration
        start_time_1 = self._parameters.start_time_1
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
