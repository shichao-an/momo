from momo.settings import settings


class Plugin(object):
    def __init__(self):
        self.settings = settings

    def setup(self):
        """Initializae the plugin"""
        raise NotImplementedError

    def run(self, extra_args=None):
        """Run the plugin

        :param extra_args: a list of command-line arguments to pass to the
            underlying plugin.
        """
        raise NotImplementedError
