from datetime import datetime, timedelta
import asyncio


class Timer():
    def __init__(self, app):
        self._valves = app['valves']
        self._parameter = app['parameter']
        self._options = app['options']
        self._log = app['log']

        self._maxDuration = int(self._parameter.get('maxDuration'))
        self._start_hour, self._start_minute = self._parameter.get(
            'startTime').split(':')
        self._start_hour = int(self._start_hour)
        self._start_minute = int(self._start_minute)
        self._running_period_end = None
        self._running_period_start = None

    async def start_async(self):
        v = self._valves.get_next()
        while True:
            try:
                if v is None:
                    # No valves in database found, system is initalizing
                    await asyncio.sleep(2)
                    v = self._valves.get_next()
                    continue
                if v.is_running == -1:
                    v = self._valves.get_next()
                    continue
                if v.is_running == 1:
                    if self._options.enable_timer_dev_mode:
                        td = timedelta(minutes=0, seconds=v.duration)
                    else:
                        td = timedelta(minutes=v.duration)

                    if datetime.now() - v.last_run > td:
                        # Laufzeit erreicht
                        await v.set_is_running(0)
                        self._log.debug("valveOff " + v.name)
                    else:
                        pass
                if v.is_running == 0:
                    if self._options.enable_timer_dev_mode:
                        td = timedelta(days=0, seconds=v.interval)
                    else:
                        td = timedelta(days=v.interval)

                    if (datetime.now() - v.last_run > td and v.is_enabled and
                            await self.is_running_period()):
                        # Intervall erreicht
                        await v.set_is_running(1)
                        self._log.debug("valveOn " + v.name)
                    else:
                        v = self._valves.get_next()
                        self._log.debug("NextValve: " + v.name)
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                self._log.debug("Timer: trapped cancel")
                break
        self._log.debug("Timer: shutdown valve")
        if v is not None:
            await v.set_is_running(0)

    async def is_running_period(self) -> bool:
        print("in function is_running_period")
        if self._running_period_start is None:
            self._running_period_start = datetime.now().replace(
                hour=self._start_hour, minute=self._start_minute)

        if datetime.now() < self._running_period_start:
            self._running_period_end = None
            return False

        if self._running_period_end is None:
            self._running_period_end = self._running_period_start + \
                timedelta(minutes=self._maxDuration)

        if datetime.now() > self._running_period_end:
            self._running_period_start = None
            return False
        print("is running period")
        return True
