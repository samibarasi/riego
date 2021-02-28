from datetime import datetime, timedelta
import asyncio
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
            c.execute("""SELECT * FROM valves
                        ORDER BY valves.prio""")
            valves = c.fetchall()
            self._db_conn.commit()

            one_valve_is_on = 0
            for valve in valves:
                if valve['is_running'] == 1:
                    one_valve_is_on = 1
                    break

            for valve in valves:
                if await self._dispatch_valve(valve, one_valve_is_on):
                    break
        # Close last valve on exit
        if valve is not None:
            await self._valves.set_off_try(valve['id'])
        return None

    async def _check_updates(self):
        return None

    async def _dispatch_valve(self, valve, one_valve_is_on):
        # _log.debug("dispatch_valve: {}".format(valve['name']))
        if not self._mqtt.client.is_connected:
            return 0
        if valve is None:
            return 0
        if valve['duration'] == 0:
            return 0
        if valve['is_running'] == 1:
            return await self._check_to_switch_off(valve)
        if valve['is_hidden']:
            return 0
        if not valve['is_enabled']:
            return 0
        if valve['is_running'] == -1:
            return 0
        if valve['is_running'] == 0 and not one_valve_is_on == 1:
            return await self._check_to_switch_on(valve)
        return 0

    async def _check_to_switch_off(self, valve) -> bool:
        """
        If we had some action, we return True
        """
        # _log.debug("check_to_switch_off for id: {}".format(valve['id']))
        if self._options.enable_timer_dev_mode:
            td = timedelta(minutes=0, seconds=valve['duration'])
        else:
            td = timedelta(minutes=valve['duration'])

        if datetime.now() - valve['last_run'] >= td:
            # Laufzeit erreicht
            await self._valves.set_off_try(valve['id'])
            _log.debug('valveOff: {}'.format(valve['name']))
            return True
        return False

    async def _check_to_switch_on(self, valve) -> bool:
        """
        If we had some action, we return True
        """
        # _log.debug("check_to_switch_on for id: {}".format(valve['id']))
        if self._options.enable_timer_dev_mode:
            td = timedelta(days=0, seconds=valve['interval'])
        else:
            td = timedelta(days=valve['interval'])

        current_shedule_datetime = await self._is_running_period()
        if (datetime.now() - valve['last_shedule'] >= td and
                current_shedule_datetime is not None):
            # Intervall erreicht
            await self._valves.set_on_try(valve['id'])
            cursor = self._db_conn.cursor()
            cursor.execute("""UPDATE valves SET
                            last_shedule = ?
                            WHERE id = ? """,
                           (current_shedule_datetime, valve['id']))
            self._db_conn.commit()
            if cursor.rowcount < 1:
                _log.error('update for last_shedule failed')
                return False
            _log.debug('valveOn: {}'.format(valve['name']))
            return True
        return False

    def _shutdown(self, task) -> None:
        _log.debug('Timer Engine shutdown called')
        self._stop = True

    async def _is_running_period(self) -> datetime:
        """Return current the sheduled "Datetime" if we have raining times

        :return: [description]
        :rtype: datetime
        """
        if self._parameters.start_time_1 is None:
            self._parameters.start_time_1 = self._options.parameters.start_time_1  # noqa: E501
        if self._parameters.max_duration is None:
            self._parameters.max_duration = self._options.parameters.max_duartion  # noqa: E501

        start_hour, start_minute = self._parameters.start_time_1.split(':')

        if self._running_period_start is None:
            self._running_period_start = datetime.now().replace(
                hour=int(start_hour), minute=int(start_minute),
                second=0, microsecond=0)

        if datetime.now() < self._running_period_start:
            self._running_period_end = None
            return None

        if self._running_period_end is None:
            self._running_period_end = self._running_period_start + \
                timedelta(minutes=self._parameters.max_duration)

        if datetime.now() > self._running_period_end:
            self._running_period_start = None
            return None
        return self._running_period_start
