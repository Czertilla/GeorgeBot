from .display import Display

class MetaBot(type):
    def __new__(cls, name, bases, attrs):
        bases = (Display,)
        return super(MetaBot, cls).__new__(cls, bases, attrs)