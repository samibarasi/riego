from datetime import datetime, timedelta
import asyncio

from riego.model.parameters import Parameter
from riego.model.valves import Valve
from riego.model.events import Event
from riego.model.boxes import Box


class Timer():
    def __init__(self, app):
        self._db = app['db']
        self._options = app['options']
        self._log = app['log']
        self._mqtt = app['mqtt']
        self._valves = app['valves']

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
        self._log.debug('Timer Engine started')
        await asyncio.sleep(3)
        self._current_valve_running = None
        while not self._stop:
            valve_ids = []
            await self._check_updates()
            session = self._db.Session()
            items = session.query(Valve).order_by(Valve.prio).all()
            for item in items:
                valve_ids.append(item.id)
            session.close()
            for valve_id in valve_ids:
                await self._dispatch_valve(valve_id)
                await asyncio.sleep(1)
#         if valve is not None:
#            await self._valves.set_off_try(valve)
        
        return None

    async def _check_updates(self):
        return None

    async def _dispatch_valve(self, valve_id):
        session = self._db.Session()
        valve = session.query(Valve).get(valve_id)
        session.commit()
        print(valve)
        if not self._mqtt.client.is_connected:
            session.close()
            return None
        if valve is None:
            session.close()
            return None
        if valve.is_running == 1:
            self._current_valve_running = valve.id
            if await self._check_to_switch_off(valve):
                self._current_valve_running = 0
                session.close()
                return 0
            else:
                session.close()
                return 1
        if valve.is_hidden:
            session.close()
            return None
        if not valve.is_enabled:
            session.close()
            return None
        if valve.is_running == -1:
            session.close()
            return None
        if valve.is_running == 0:
            if (not self._current_valve_running and
                    await self._check_to_switch_on(valve)):
                self._current_valve_running = valve.id
                session.close()
                return 1
        session.close()
        return None
    
    async def _check_to_switch_off(self, valve) -> bool:
        ret = False
        print(f"check off id: {valve.id}")
        if self._options.enable_timer_dev_mode:
            td = timedelta(minutes=0, seconds=valve.duration)
        else:
            td = timedelta(minutes=valve.duration)

        if datetime.now() - valve.last_shedule > td:
            # Laufzeit erreicht
            await self._valves.set_off_try(valve.id)
            self._log.debug('valveOff: {}'.format(valve.name))
            ret = True
        return ret

    async def _check_to_switch_on(self, valve) -> bool:
        ret = False
        print(f"check on id: {valve.id}")
        if self._options.enable_timer_dev_mode:
            td = timedelta(days=0, seconds=valve.interval)
        else:
            td = timedelta(days=valve.interval)

        if (datetime.now() - valve.last_shedule > td and
                await self._is_running_period()):
            # Intervall erreicht
            await self._valves.set_on_try(valve.id)
            valve.last_shedule = datetime.now()
            self._log.debug('valveOn: {}'.format(valve.name))
            ret = True
        return ret

    def _shutdown(self, task) -> None:
        self._log.debug('Timer Engine shutdown called')
        self._stop = True

    async def _is_running_period(self) -> bool:
        return True
        session = self._db.Session()
        self._maxDuration = session.query(Parameter).filter(
            Parameter.key == 'maxDuration').first().value
        self._startTime = session.query(Parameter).filter(
            Parameter.key == 'startTime').first().value
        session.close()
        self._start_hour, self._start_minute = self._startTime.split(':')
        self._start_hour = int(self._start_hour)
        self._start_minute = int(self._start_minute)

        if self._running_period_start is None:
            self._running_period_start = datetime.now().replace(
                hour=self._start_hour, minute=self._start_minute, second=0)

        if datetime.now() < self._running_period_start:
            self._running_period_end = None
            return False

        if self._running_period_end is None:
            self._running_period_end = self._running_period_start + \
                timedelta(minutes=self._maxDuration)

        if datetime.now() > self._running_period_end:
            self._running_period_start = None
            return False
        return True
