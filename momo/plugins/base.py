from momo.settings import settings


class Plugin(object):
    def __init__(self):
        self.settings = settings

    def setup(self):
        """Initializae the plugin"""
        raise NotImplementedError

    def run(self):
        """Run the plugin"""
        raise NotImplementedError
