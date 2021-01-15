import paho.mqtt.client
import asyncio


class Mqtt:
    def __init__(self, app):
        options = app['options']
        self.__log = app['log']
        self.client = paho.mqtt.client.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.connect(options.mqtt_host, options.mqtt_port, 10)
        self.__wait_for_first_conn()

    def __wait_for_first_conn(self):
        self.client.loop()
        self.client.loop()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.client.subscribe("cmnd/controler/#")
            self.__log.info("Mqtt Connection established")
        else:
            self.__log.critical("Bad mqtt connection, rc: " + str(rc))

    # The callback for when a PUBLISH message is received from the server.

    def _on_message(self, client, userdata, msg):
        self.__log.debug("catch all " + msg.topic+" "+str(msg.payload))

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.__log.error(
                "Unexpected mqtt disconnection rc: " + str(rc))

    async def start_async(self):
        while True:
            try:
                # TODO: convert to Task
                self.client.loop()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                self.__log.debug("mqtt: trapped cancel")
                break
        self.client.disconnect()
