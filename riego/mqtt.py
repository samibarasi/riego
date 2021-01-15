import asyncio

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311


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
        self.client.subscribe('TEST/#', qos=0)

    def _on_message(self, client, topic, payload, qos, properties):
        self.__log.debug('MQTT RECV MSG:', payload)

    def _on_disconnect(self, client, packet, exc=None):
        self.__log.debug('MQTT Disconnected')

    def _on_subscribe(self, client, mid, qos, properties):
        self.__log.debug('MQTT SUBSCRIBED')

    async def start_async(self):
        await self.client.connect(self.__options.mqtt_host,
                                  port=self.__options.mqtt_port,
                                  keepalive=10,
                                  version=MQTTv311)
        while True:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                self.__log.debug('MQTT: trapped cancel')
                break
        await self.client.disconnect()
