# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from momo.utils import txt_type, PY3

ROOT_NODE_NAME = '(root)'


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


class Bucket(Base):
    """
    The Bucket class.

    :param document: a BucketDocument object

    """
    def __init__(self, document):
        self.document = document
        self.name = self.document.name
        self._content = None
        self._root = None
        self.load()

    @property
    def content(self):
        return self._content

    def load(self):
        self._content = self.document.load()

    def save(self):
        self.document.dump(self._contents.to_dict())

    @property
    def root(self):
        """
        Get the root node.
        """
        if self._root is None:
            root = Node(name=ROOT_NODE_NAME,
                        bucket=self.bucket,
                        parent=None)
            self._root = root
        return self._root

    def __unicode__(self):
        return self.name


class Element(Base):
    """
    The Element class.
    """
    def __init__(self, name, bucket, parent):
        self.name = self.name
        self.bucket = self.bucket


class Node(Element):
    """
    The Node class.
    """
    def __init__(self, name, bucket, parent, content):
        super(Node, self).__init__(name, bucket, parent)
        self.kind = 'Node'
        self.content = content
        self._elements = None

    def elements(self):
        if self._elements is None:
            is_dir = False
            is_file = False
            self._elements = []
            for name in self.content:
                if isinstance(self.content['name'], str):
                    is_file = True
                    element = Attribute(name=name,
                                        bucket=self.bucket,
                                        parent=self)
                else:
                    is_dir = True
                    element = Node(name=name,
                                   bucket=self.bucket,
                                   parent=self,
                                   content=self.content['name'])
            self._elements.append(element)
        if is_dir is True:
            self.kind = 'Directory'
        elif is_file is True:
            self.kind = 'File'
        return self._elements

    def __unicode__(self):
        return '%s: %s' % (self.kind, self.name)


class Attribute(Element):
    """
    The Attribute class.
    """
    def __init__(self, name, bucket, parent):
        super(Attribute, self).__init__(name, bucket, parent)
