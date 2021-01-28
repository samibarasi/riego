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
        self._subscriptions = {}

        self._task = None
        app.cleanup_ctx.append(self.mqtt_engine)

    async def mqtt_engine(self, app):
        self._task = asyncio.create_task(self._startup(app))
        yield
        # TODO _shutdown should not be an awaitable
        await self._shutdown(app, self._task)

    async def _startup(self, app) -> None:
        self._log.debug('MQTT Engine startup called')
        await self.client.connect(self._options.mqtt_host,
                                  port=self._options.mqtt_port,
                                  keepalive=10,
                                  version=MQTTv311)
        return None

    async def _shutdown(self, app, task) -> None:
        self._log.debug('MQTT Engine shutdown called')
        # TODO hier kein awaitable sinnvoll
        await self.client.disconnect()
        return None

    def _on_connect(self, client, flags, rc, properties):
        self._log.debug('MQTT Connected')

        for key in self._subscriptions:
            self.client.subscribe(key, qos=0)

    async def _on_message(self, client, topic, payload, qos, properties):
        payload = payload.decode()
#        self._log.debug(f'MQTT RECV MSG: {payload}, TOPIC: {topic}')
        for key in self._subscriptions:
            if self.match_topic(topic, key):
                func = self._subscriptions[key]
                try:
                    await func(topic, payload)
                except Exception as e:
                    self._log.error(
                        f'{__name__}, exeption {e} in callable {func}')
        return 0

    def _on_disconnect(self, client, packet, exc=None):
        self._log.debug('MQTT Disconnected')

    def _on_subscribe(self, client, mid, qos, properties):
        self._log.debug('MQTT SUBSCRIBED')

    def subscribe(self, topic: str, callback: callable) -> None:
        self._subscriptions[topic] = callback
# TODO only subscription from callbacks are possible,
# because client is not connected in this momen

#    Der MQTT Client ist noch nicht gestartet.
#    Subscribe ist noch nicht möglich.
#        self.client.subscribe(topic, qos=0)
        return None

    def match_topic(self, topic: str, sub: str) -> bool:
        # Achtung auch "stat/+/RESULT" und "stat/+/RESULT1234"
        # ergebn ein Match! Die regex ist nicht korrekt!
        ret = bool(re.match(sub.translate({43: "[^/]+", 35: ".+"}), topic))
        return ret


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
