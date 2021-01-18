from datetime import datetime, timedelta
import asyncio


class Timer():
    def __init__(self, app):
        self.__log = app['log']
        self.__valves = app['valves']
        self.__parameter = app['parameter']
        self.__options = app['options']

    async def start_async(self):
        v = self.__valves.get_next()
        while True:
            try:
                if v.is_running:
                    td = timedelta(minutes=v.duration)
                    if self.__options.enable_timer_dev_mode:
                        td = timedelta(minutes=0, seconds=v.duration)

                    if datetime.now() - v.last_run > td:
                        # Laufzeit erreicht
                        await v.set_is_running(0)
                        self.__log.debug("valveOff " + v.name)
                    else:
                        pass
                else:
                    td = timedelta(days=v.interval)
                    if self.__options.enable_timer_dev_mode:
                        td = timedelta(days=0, seconds=v.interval)

                    if (datetime.now() - v.last_run > td and v.is_enabled and
                            datetime.now().strftime('%H:%M') >=
                            self.__parameter.get('startTime')):
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
