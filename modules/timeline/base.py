class Timeline(object):
    def __init__(self, **kwargs):
        raise NotImplementedError

    def addEvent(self, **kwargs):
        raise NotImplementedError

    def addEventSource(self, **kwargs):
        raise NotImplementedError

    def generateCode(self):
        raise NotImplementedError


