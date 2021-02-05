from riego.model.parameters import Parameter

defaults = {
    'maxDuration': '240',
    'startTime': '19:00',
}


class Parameters:
    def __init__(self, app):
        session = app['db'].Session()
        for key in defaults:
            item = session.query(Parameter).filter(
                Parameter.key == key).first()
            if item is None:
                p = Parameter(key=key, value=defaults[key])
                session.add(p)
        session.commit()
        session.close()
