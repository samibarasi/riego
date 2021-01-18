import os
import logging
import time

import asyncio
import mqttools


class Mqtt:
    def __init__(self, app):
        self.__options = app['options']
        self.__log = app['log']

        self.client = mqttools.Client(self.__options.mqtt_host,
                                      self.__options.mqtt_port,
                                      client_id=self.__options.mqtt_client_id)

    async def start_async(self):

        await self.client.start()
        await self.client.subscribe(self.__options.mqtt_subscription_topic)

        try:
            while True:
                topic, message = await self.client.messages.get()

                if topic is None:
                    print('Broker connection lost!')
                    break

                print(f'Topic:   {topic}')
                print(f'Message: {message}')
        except asyncio.CancelledError:
            await self.client.disconnect()

#        while True:
#            try:
#                await asyncio.sleep(1)
#            except asyncio.CancelledError:
#                self.__log.debug('MQTT: trapped cancel')
#                break
#        self.__log.debug('MQTT: call disconnect()')
#        await self.client.disconnect()


class Options():

    def __init__(self):
        self.mqtt_host = "192.168.88.229"
        self.mqtt_port = 1883
        self.mqtt_client_id = "testing"
        self.mqtt_subscription_topic = "riego/#"


async def main():
    app = {}
    options = Options()
    app['options'] = options
    app['log'] = logging.getLogger()

    mqttc = Mqtt(app)
    await mqttc.start_async()

    mqttc.client.publish('riego/TEST/TIME', str(time.time()), qos=1)

    await asyncio.sleep(6)
    await mqttc.client.disconnect()


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.DefaultEventLoopPolicy = asyncio.WindowsSelectorEventLoopPolicy
    asyncio.run(main())
