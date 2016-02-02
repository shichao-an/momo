import backends
from utils import eval_path
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
    _backend = 'yaml'

    def __init__(self, backend='yaml'):

        self._backend = backend
        self._buckets = None
        self._document = None

    def from_file(self):
        if os.path.exists(SETTINGS_FILE):
            with open() as f:
                self._document = yaml.load(f.read())

    def _get_default_bucket(self):
        filetypes = BUCKET_FILE_TYPES[self._backend]

        for ft in filetypes:
            bucket = os.path.join(PROJECT_PATH, 'momo' + ft)
            if os.path.exists(bucket):
                return bucket

        for ft in filetypes:
            bucket = os.path.join(eval_path('~'), '.momo' + ft)
            if os.path.exists(bucket):
                return bucket

    @property
    def buckets(self):
        """
        Get buckets as a dictionary.

        :return: a dictionary of buckets

        """
        if self._document is not None:
            if 'buckets' in self._document:
                self._buckets = self._document['buckets']
        if self._buckets is None:
            bucket = self._get_default_bucket()
            self.buckets['default'] = bucket
        return self._buckets

    @property
    def bucket(self):
        """
        Get the default bucket.  The default bucket can be the value of the
        environment variable `MOMO_BUCKET`, a path in the default location
        that matches the backend type, the value of the `default` key (if it
        exists) in buckets, whichever is available first.

        :return: path to the default bucket
        :rtype: str

        """
        bucket = None
        if 'MOMO_BUCKET' in os.environ:
            bucket = os.environ['MOMO_BUCKET']
        elif 'default' in self.buckets:
            bucket = self.buckets['default']
        else:
            bucket = self._get_default_bucket()
        if bucket is None:
            raise SettingsError('default bucket is not found')
        return bucket

    @property
    def backend(self):
        return getattr(backends, self._backend)

settings = Settings()
settings.from_file()
