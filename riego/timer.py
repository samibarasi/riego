from datetime import datetime, timedelta
import asyncio
from sqlite3 import Row


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

        self._stop = False
        self._task = None
        app.cleanup_ctx.append(self.timer_engine)

    async def timer_engine(self, app):
        self._task = asyncio.create_task(self._my_loop())
        yield
        self._stop = True
        self._log.debug('Timer stop called')
        # self.__task.cancel()

    async def _my_loop(self) -> None:
        while not self.__stop:
            valves = await self._valves.fetch_all()
            valve_name = valves[0]['name']
            print(f'next: {valve_name}')
            await asyncio.sleep(1)
        # TODO close last valve
        return None

    async def _is_running_period(self) -> bool:
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
        return True
