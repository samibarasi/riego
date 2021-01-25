import asyncio
import logging
import re

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311


class Mqtt:
    def __init__(self, app):
        self._options = app['options']
        self._log = app['log']
        self.client = MQTTClient(self._options.mqtt_client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe
        self.subscriptions = {}

    def _on_connect(self, client, flags, rc, properties):
        self._log.debug('MQTT Connected')

        for key in self.subscriptions:
            self.client.subscribe(key, qos=0)

    async def _on_message(self, client, topic, payload, qos, properties):
        payload = payload.decode()
#        self._log.debug(f'MQTT RECV MSG: {payload}, TOPIC: {topic}')
        for key in self.subscriptions:
            if self.match_topic(topic, key):
                func = self.subscriptions[key]
                await func(topic, payload)
        return 0

    def _on_disconnect(self, client, packet, exc=None):
        self._log.debug('MQTT Disconnected')

    def _on_subscribe(self, client, mid, qos, properties):
        self._log.debug('MQTT SUBSCRIBED')

    async def start_async(self):
        await self.client.connect(self._options.mqtt_host,
                                  port=self._options.mqtt_port,
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

    def subscribe(self, topic: str, callback: callable) -> None:
        self.subscriptions[topic] = callback

#    Der MQTT Client ist noch nicht gestartet.
#    Subscribe ist noch nicht möglich.
#        self.client.subscribe(topic, qos=0)
        return None

    def match_topic(self, topic: str, sub: str) -> bool:
        # Achtung auch "stat/+/RESULT" und "stat/+/RESULT1234"
        # ergebn ein Match! Die regex ist nicht korrekt!
        ret = bool(re.match(sub.translate({43: "[^/]+", 35: ".+"}), topic))
        return ret

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
