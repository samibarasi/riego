import asyncio
import logging

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311


"""
Der connect zum MQTT-Broker findet mit so großer Verzögerung statt,
dass duie ersten "publishes" verloren gehen.
gmqtt prüft leider nicht, ob der socket schon verbunden ist, bevor 
er Nachrichten sendet


"""


class Mqtt:
    def __init__(self, app):
        self.__options = app['options']
        self.__log = app['log']
        self.client = MQTTClient(self.__options.mqtt_client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe

    def _on_connect(self, client, flags, rc, properties):
        self.__log.debug('MQTT Connected')
        self.client.subscribe('stat/#', qos=0)

    def _on_message(self, client, topic, payload, qos, properties):
        self.__log.debug(f'MQTT RECV MSG: {payload}, TOPIC: {topic}')

    def _on_disconnect(self, client, packet, exc=None):
        self.__log.debug('MQTT Disconnected')

    def _on_subscribe(self, client, mid, qos, properties):
        self.__log.debug('MQTT SUBSCRIBED')

    async def start_async(self):
        await self.client.connect(self.__options.mqtt_host,
                                  port=self.__options.mqtt_port,
                                  keepalive=10,
                                  version=MQTTv311)

#        while True:
#            try:
#                await asyncio.sleep(1)
#            except asyncio.CancelledError:
#                self.__log.debug('MQTT: trapped cancel')
#                break
#        self.__log.debug('MQTT: call disconnect()')
#        await self.client.disconnect()

    async def shutdown(self):
        await self.client.disconnect()


# Manually create Mock-Object


class Options():

    def __init__(self):
        self.mqtt_host = "192.168.88.229"
        self.mqtt_port = 1883
        self.mqtt_client_id = "testing"


async def main():
    app = {}
    options = Options()
    app['options'] = options
    logger = logging
    logging.basicConfig(level=logging.DEBUG)
    app['log'] = logger

    mqttc = Mqtt(app)
    await mqttc.start_async()

    mqttc.client.publish('cmnd/dev01/POWER1', payload="ON", qos=1)

    try:
        await asyncio.sleep(60)
    except asyncio.CancelledError:
        print('MQTT: trapped cancel')
    finally:
        await mqttc.client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
