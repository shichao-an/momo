from momo import backends
from momo.core import Bucket
from momo.utils import eval_path
import os
import yaml


SETTINGS_FILE = eval_path('~/.momo')
BUCKET_FILE_TYPES = {
    'yaml': ('.yaml', '.yml')
}
PROJECT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))


class SettingsError(Exception):
    pass


class Settings(object):
    """
    The Settings class.

    :param backend: the backend type

    """

    # default settings
    _defaults = {
        'backend': 'yaml',
        'lazy_bucket': True
    }

    def __init__(self, backend=None):

        self._backend = backend or self._defaults['backend']
        self._buckets = None
        self._settings = None

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            with open() as f:
                self._settings = yaml.load(f.read())

    def _get_default_bucket_path(self):
        path = os.environ.get('MOMO_DEFAULT_BUCKET')
        if path is not None:
            return path
        filetypes = BUCKET_FILE_TYPES[self._backend]
        for ft in filetypes:
            path = os.path.join(PROJECT_PATH, 'momo' + ft)
            if os.path.exists(path):
                return path
        for ft in filetypes:
            path = os.path.join(eval_path('~'), '.momo' + ft)
            if os.path.exists(path):
                return path
        raise SettingsError('default bucket is not found')

    @property
    def buckets(self):
        """
        Get buckets as a dictionary.

        :return: a dictionary of buckets

        """
        if self._settings is not None:
            if 'buckets' in self._settings:
                self._buckets = {
                    name: self._to_bucket(name, path)
                    for name, path in self._settings['buckets'].items()
                }
        if self._buckets is None:
            name = 'default'
            path = self._get_default_bucket_path()
            self._buckets = {
                name: self.to_bucket(name, path)
            }
        return self._buckets

    def to_bucket(self, name, path):
        BucketDocument = getattr(self.backend, 'BucketDocument')
        document = BucketDocument(name, path)
        return Bucket(document, self)

    @property
    def bucket(self):
        """
        Get the default bucket.

        """
        return self.buckets['default']

    @property
    def backend(self):
        return getattr(backends, self._backend)

    def __getattr__(self, name):
        res = None
        if self._settings is not None:
            res = self._settings.get(name)
        if res is None:
            res = self._defaults.get(name)
        if res is None:
            raise SettingsError('"%s" setting is not found' % name)
        return res


settings = Settings()
settings.load()
