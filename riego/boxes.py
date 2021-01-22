

class Boxes():
    def __init__(self, app):
        self.mqtt = app['mqtt']
#        self._subscribe()

    def _my_callback(self, msg):
        print(f'Payload: {msg.payload}, Topic: {msg.topic}')

    def _subscribe(self):
        self.mqtt.subscribe("stat/#", self._my_callback)
