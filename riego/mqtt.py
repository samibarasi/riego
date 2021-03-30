import asyncio
import re

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311

from logging import getLogger
_log = getLogger(__name__)

_instance = None


def get_mqtt():
    global _instance
    return _instance


def setup_mqtt(app=None, options=None):
    global _instance
    if _instance is not None:
        del _instance
    _instance = Mqtt(app=app, options=options)
    return _instance


class Mqtt:
    def __init__(self, app=None, options=None):
        global _instance
        if _instance is None:
            _instance = self

        self._options = options
        self.client = MQTTClient(self._options.mqtt_client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe
        self._subscriptions = {}

        app.cleanup_ctx.append(self._mqtt_engine)

    async def _mqtt_engine(self, app):
        task = asyncio.create_task(self._startup(app))
        yield
        # TODO _shutdown should not be an awaitable
        await self._shutdown(app, task)

    async def _startup(self, app) -> None:
        _log.debug('MQTT Engine startup called')
        await self.client.connect(self._options.mqtt_broker_host,
                                  port=self._options.mqtt_broker_port,
                                  keepalive=10,
                                  version=MQTTv311)
        return None

    async def _shutdown(self, app, task) -> None:
        _log.debug('MQTT Engine shutdown called')
        # TODO hier kein awaitable sinnvoll
        await self.client.disconnect()
        return None

    def _on_connect(self, client, flags, rc, properties):
        _log.debug('MQTT Connected')

        for key in self._subscriptions:
            self.client.subscribe(key, qos=0)

    async def _on_message(self, client, topic, payload, qos, properties):
        payload = payload.decode()
#        _log.debug(f'MQTT RECV MSG: {payload}, TOPIC: {topic}')
        for key in self._subscriptions:
            if self.match_topic(topic, key):
                func = self._subscriptions[key]
                try:
                    await func(topic, payload)
                except Exception as e:
                    _log.error(
                        f'{__name__}, exeption {e} in callable {func}')
        return 0

    def _on_disconnect(self, client, packet, exc=None):
        _log.debug('MQTT Disconnected')

    def _on_subscribe(self, client, mid, qos, properties):
        _log.debug('MQTT SUBSCRIBED')

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
        self.mqtt_broker_host = "192.168.88.229"
        self.mqtt_broker_port = 1883
        self.mqtt_client_id = "testing"


async def main():
    app = {}
    options = Options()
    app['options'] = options

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
