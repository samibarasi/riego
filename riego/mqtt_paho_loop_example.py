import socket
import paho.mqtt.client as mqtt
import asyncio


import time
import logging
import os


class AsyncioHelper:
    def __init__(self, loop, client):
        self.loop = loop
        self.client = client
        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write

    def on_socket_open(self, client, userdata, sock):
        print("Socket opened")

        def cb():
            print("Socket is readable, calling loop_read")
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        print("Socket closed")
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        print("Watching socket for writability.")

        def cb():
            print("Socket is writable, calling loop_write")
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        print("Stop watching socket for writability.")
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        print("misc_loop started")
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
        print("misc_loop finished")


class Mqtt:
    def __init__(self, app):
        self.__options = app['options']
        self.__log = app['log']
        self.__loop = asyncio.get_event_loop()
        self.got_message = None

        self.client = mqtt.Client(client_id=self.__options.mqtt_client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        aioh = AsyncioHelper(self.__loop, self.client)

    def _on_connect(self, client, userdata, flags, rc):
        self.__log.debug('MQTT Connected')
        client.subscribe('TEST/#', qos=0)

    def _on_message(self, client, userdata, msg):
        self.__log.debug('MQTT RECV MSG:' + str(msg))
        print('MQTT RECV MSG:' + str(msg))
#        if not self.got_message:
#            print("Got unexpected message: {}".format(msg.decode()))
#        else:
#            self.got_message.set_result(msg.payload)

    def _on_disconnect(self, client, userdata, rc):
        self.disconnected.set_result(rc)
        self.__log.debug('MQTT Disconnected')
#        exit(1)

    async def start_async(self):

        self.client.connect(self.__options.mqtt_host,
                            self.__options.mqtt_port, 10)
        self.client.socket().setsockopt(socket.SOL_SOCKET,
                                        socket.SO_SNDBUF,
                                        2048)

        while True:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                self.__log.debug('MQTT: trapped cancel')
                break
        self.__log.debug('MQTT: call disconnect()')
        await self.client.disconnect()


class Options():

    def __init__(self):
        self.mqtt_host = "192.168.88.229"
        self.mqtt_port = 1883
        self.mqtt_client_id = "testing"


async def main():
    app = {}
    options = Options()
    app['options'] = options
    app['log'] = logging.getLogger()

    mqttc = Mqtt(app)
    await mqttc.start_async()

    mqttc.client.publish('TEST/TIME', str(time.time()), qos=1)

    await asyncio.sleep(6)
    await mqttc.client.disconnect()


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.DefaultEventLoopPolicy = asyncio.WindowsSelectorEventLoopPolicy
    asyncio.run(main())
