from datetime import datetime, timedelta
import asyncio


class Timer():
    def __init__(self, app):
        self._valves = app['valves']
        self._parameters = app['parameters']
        self._options = app['options']
        self._log = app['log']
        self._mqtt = app['mqtt']

        self._running_period_end = None
        self._running_period_start = None

        self._stop = False
        self._task = None
        app.cleanup_ctx.append(self.timer_engine)

    async def timer_engine(self, app):
        self._task = asyncio.create_task(self._startup(app))
        yield
        self._shutdown(app, self._task)

    async def _startup(self, app) -> None:
        self._log.debug('Timer Engine startup called')
        valve = await self._valves.get_next(None)
        while not self._stop:
            await self._check_updates()
            await asyncio.sleep(1)
            if not self._mqtt.client.is_connected:
                await asyncio.sleep(3)
                continue
            if valve is None:
                await asyncio.sleep(3)
                valve = await self._valves.get_next(valve)
                continue
            print(int(valve['is_running']))
            if int(valve['is_running']) == 1:
                if await self._check_to_switch_off(valve):
                    valve = await self._valves.get_next(valve)
                    #TODO another SELECT is neccessary to update valve
                    #################################################

                await asyncio.sleep(1)
                continue
            if valve['is_hidden']:
                valve = await self._valves.get_next(valve)
                continue
            if not valve['is_enabled']:
                valve = await self._valves.get_next(valve)
                continue
            if int(valve['is_running']) == 0:
                if not await self._check_to_switch_on(valve):
                    #TODO another SELECT is neccessary to update valve
                    #################################################
                    valve = await self._valves.get_next(valve)
                await asyncio.sleep(3)
                continue
            if int(valve['is_running']) == -1:
                valve = await self._valves.get_next(valve)
                continue

            
            await asyncio.sleep(1)
        if valve is not None:
            await self._valves.set_off_try(valve)
        return None

    async def _check_updates(self):
        return None

    async def _check_to_switch_off(self, valve) -> bool:
        ret = False
        print(f"check off id: {valve['name']}")
        if self._options.enable_timer_dev_mode:
            td = timedelta(minutes=0, seconds=valve['duration'])
        else:
            td = timedelta(minutes=valve['duration'])

        last_shedule = datetime.strptime(
            valve['last_shedule'], self._options.time_format)
        if datetime.now() - last_shedule > td:
            # Laufzeit erreicht
            await self._valves.set_off_try(valve)
            self._log.debug('valveOff: {}'.format(valve['name']))
            ret = True
        return ret

    async def _check_to_switch_on(self, valve) -> bool:
        ret = False
        print(f"check on id: {valve['name']}")
        if self._options.enable_timer_dev_mode:
            td = timedelta(days=0, seconds=valve['interval'])
        else:
            td = timedelta(days=valve['interval'])

        last_shedule = datetime.strptime(
            valve['last_shedule'], self._options.time_format)
        if (datetime.now() - last_shedule > td and
                await self._is_running_period()):
            # Intervall erreicht
            await self._valves.set_on_try(valve)
            last_shedule = self._running_period_start.strftime(
                self._options.time_format)
            await self._valves.update_by_key(valve['id'],
                                             'last_shedule',
                                             last_shedule)
            self._log.debug('valveOn: {}'.format(valve['name']))
            ret = True
        return ret

    def _shutdown(self, app, task) -> None:
        self._log.debug('Timer Engine shutdown called')
        self._stop = True

    async def _is_running_period(self) -> bool:
        self._maxDuration = int(self._parameters.get('maxDuration'))
        self._start_hour, self._start_minute = self._parameters.get(
            'startTime').split(':')
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
