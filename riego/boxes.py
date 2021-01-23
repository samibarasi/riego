

class Boxes():
    def __init__(self, app):
        self.mqtt = app['mqtt']
        self.mqtt.subscribe('tele/#', self._mqtt_handler)

    async def _mqtt_handler(self, topic: str, payload: str) -> bool:
        print(f'Topic: {topic}, payload: {payload}')
        return True
