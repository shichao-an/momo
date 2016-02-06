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
    def __init__(self, document, settings):
        self.document = document
        self.settings = settings
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
            root = Directory(name=ROOT_NODE_NAME,
                             bucket=self,
                             parent=None,
                             content=self.content)
            self._root = root
        return self._root

    def __unicode__(self):
        return txt_type(self.name)


class Element(Base):
    """
    The Element class.
    """
    def __init__(self, name, bucket, parent, content):
        self.name = name
        self.bucket = bucket
        self.parent = parent
        self.content = content

    def __unicode__(self):
        return txt_type(self.name)


class Node(Element):
    """
    The Node class.
    """
    def __init__(self, name, bucket, parent, content):
        super(Node, self).__init__(name, bucket, parent, content)
        self._elems = None
        self._vals = None
        self._i = 0
        self._len = None
        if not self.bucket.settings.lazy_bucket:
            # self.elems is called here so that the next-level elements are
            # loaded and the classes of the current elements are updated
            self._len = len(self.elems)

    @property
    def elems(self):
        """
        Get elements of this node.
        """
        if self._elems is None:
            is_dir = False
            is_file = False
            self._elems = {}
            for name in self.content:
                content = self.content[name]
                is_dict = isinstance(content, dict)
                is_list = isinstance(content, list)
                if not is_dict and not is_list:
                    is_file = True
                    elem = \
                        Attribute(name=name,
                                  bucket=self.bucket,
                                  parent=self,
                                  content=content)
                else:
                    is_dir = True
                    elem = Node(name=name,
                                bucket=self.bucket,
                                parent=self,
                                content=content)
                self._elems[name] = elem
            if is_dir is True:
                self.__class__ = Directory
            elif is_file is True:
                self.__class__ = File
            self._vals = self._elems.values()
        return self._elems

    @property
    def vals(self):
        if self._elems is None:
            self._vals = self.elems.values()
        return self._vals

    @property
    def attrs(self):
        return filter(lambda x: isinstance(x, Attribute), self.elems)

    def __iter__(self):
        return self

    def __next__(self):
        if self._len is None:
            self._len = len(self.elems)
        if self._i < self._len:
            i = self._i
            self._i += 1
            return self.vals[i]
        else:
            raise StopIteration

    def next(self):
        return self.__next__()

    @property
    def level(self):
        parent = self.parent
        res = 0
        while parent is not None:
            parent = parent.parent
            res += 1
        return res

    def ls(self, name_or_num=None):
        """
        List and print elements of the Node object.
        """
        if name_or_num is None:
            self._ls_all()
        else:
            pass

    def _ls_all(self):
        indent = '  ' * self.level
        args = []
        if len(indent) > 0:
            args.append(indent)
        for elem in self.elems:
            args.append(elem)
            print(*args)
            args.pop()


class Directory(Node):
    pass


class File(Node):
    pass


class Attribute(Element):
    pass
