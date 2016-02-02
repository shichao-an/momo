# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from momo.utils import txt_type, PY3
from settings import settings
import addict


class Base(object):
    def __repr__(self):
        try:
            u = self.__str__()
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        repr_type = type(u)
        return repr_type('<%s: %s>' % (self.__class__.__name__, u))

    def __str__(self):
        if hasattr(self, '__unicode__'):
            if PY3:
                return self.__unicode__()
            else:
                return unicode(self).encode('utf-8')
        return txt_type('%s object' % self.__class__.__name__)


class Document(Base):
    """
    The Document class, corresponding to the Bucket class in the backend.

    :param bucket: the name of the bucket.

    """
    def __init__(self, bucket):
        path = settings.buckets[bucket]
        self.bucket = settings.backend.Bucket(bucket, path)
        self.name = self.bucket['name']

    def save(self):
        pass


class Directory(Base):
    def __init__(self, name):
        pass
