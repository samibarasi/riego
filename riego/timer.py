from datetime import datetime, timedelta
import asyncio


class Timer():
    def __init__(self, app):
        self.__valves = app['valves']
        self.__parameter = app['parameter']
        self.__options = app['options']
        self.__log = app['log']

        self.maxDuration = self.__parameter.get('maxDuration')
        self.start_hour, self.start_minute = self.__parameter.get(
            'startTime').split(':')
        self.start_hour = int(self.start_hour)
        self.start_minute = int(self.start_minute)
        self.__end_time = None
        self.__start_time = None

    async def start_async(self):
        v = self.__valves.get_next()
        while True:
            try:
                if v.is_running:
                    if self.__options.enable_timer_dev_mode:
                        td = timedelta(minutes=0, seconds=v.duration)
                    else:
                        td = timedelta(minutes=v.duration)

                    if datetime.now() - v.last_run > td:
                        # Laufzeit erreicht
                        await v.set_is_running(0)
                        self.__log.debug("valveOff " + v.name)
                    else:
                        pass
                else:
                    if self.__options.enable_timer_dev_mode:
                        td = timedelta(days=0, seconds=v.interval)
                    else:
                        td = timedelta(days=v.interval)

                    if (datetime.now() - v.last_run > td and v.is_enabled and
                       self.is_running_time()):
                        # Intervall erreicht
                        await v.set_is_running(1)
                        self.__log.debug("valveOn " + v.name)
                    else:
                        v = self.__valves.get_next()
                        self.__log.debug("NextValve: " + v.name)
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                self.__log.debug("Timer: trapped cancel")
                break
        self.__log.debug("Timer: shutdown valve")
        await v.set_is_running(0)

    def is_running_time(self) -> bool:
        if self.__start_time is None:
            self.__start_time = datetime.now().replace(
                hour=self.start_hour, minute=self.start_minute)

        if datetime.now() < self.__start_time:
            self.__end_time = None
            return False

        if self.__end_time is None:
            self.__end_time = self.__start_time + \
                timedelta(minutes=int(self.maxDuration))

        if datetime.now() > self.__end_time:
            self.__start_time = None
            return False

        return True
