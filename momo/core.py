# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from operator import attrgetter
from momo.utils import txt_type, PY3, utf8_decode
from momo.actions import NodeAction, AttributeAction
from momo.backends import OrderedDict
import sys


ROOT_NODE_NAME = '(root)'
PLACEHOLDER = '__placeholder__'


# Runtime configurations
class Configs(object):
    CONFIGS = {}

    def __getattr__(self, name):
        return self.CONFIGS[name]

    def __setattr__(self, name, value):
        self.CONFIGS[name] = value


configs = Configs()


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

    def dump(self):
        self.document.dump(self.content)

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
        """
        :param no_output: whether to suppress output.
        """
        self.name = name
        self.bucket = bucket
        self.parent = parent
        self.content = content
        if parent is None:
            self.path = []
        else:
            self.path = parent.path[:]
            self.path.append(self.name)
        self._action = None

    @property
    def action(self):
        return self._action

    @property
    def level(self):
        parent = self.parent
        res = 0
        while parent is not None:
            parent = parent.parent
            res += 1
        return res

    @property
    def is_node(self):
        return isinstance(self, Node)

    @property
    def is_file(self):
        return isinstance(self, File)

    @property
    def is_dir(self):
        return isinstance(self, Directory)

    @property
    def is_attr(self):
        return isinstance(self, Attribute)

    def ls(self, *args, **kwargs):
        raise NotImplementedError

    @property
    def type(self):
        """Return type of the element as a string."""
        return self.__class__.__name__

    def __unicode__(self):
        return txt_type(self.name)


class Node(Element):
    """
    The Node class.
    """
    def __init__(self, name, bucket, parent, content, *args, **kwargs):
        super(Node, self).__init__(name, bucket, parent, content,
                                   *args, **kwargs)
        self._elems = None
        self._vals = None
        self._i = 0
        self._len = None
        if not self.bucket.settings.lazy_bucket:
            # self.elems is called here so that the next-level elements are
            # loaded and the classes of the current elements are updated
            self._len = len(self.elems)
        self._action = NodeAction(self)

    @property
    def is_root(self):
        return self.parent is None

    @property
    def elems(self):
        """
        Get elements of this node.
        """
        if self._elems is None:
            this_is_dir = False
            this_is_file = False
            self._elems = OrderedDict()
            if not isinstance(self.content, dict):
                raise NodeError('invalid content format')
            for name in self.content:
                content = self.content[name]
                elem, this_is_dir, this_is_file = self._make_elem(name,
                                                                  content)
                self._elems[name] = elem
            self._update_class(this_is_dir, this_is_file)
            self._vals = self._elems.values()
        return self._elems

    def _update_class(self, this_is_dir, this_is_file):
        """Update node's class to Directory or File."""
        if this_is_dir is True:
            self.__class__ = Directory
        elif this_is_file is True:
            self.__class__ = File

    def _make_elem(self, name, content):
        """
        Make a proper element based on the content.

        :return: new child element, whether self should be a file, and whether
                 self should be a directory.
        """
        this_is_dir = self.is_dir
        this_is_file = self.is_file
        is_dict = isinstance(content, dict)
        if not is_dict:
            this_is_file = True
            elem = (
                Attribute(name=name,
                          bucket=self.bucket,
                          parent=self,
                          content=content)
            )
        else:
            this_is_dir = True
            elem = Node(name=name,
                        bucket=self.bucket,
                        parent=self,
                        content=content)
        return elem, this_is_dir, this_is_file

    @property
    def svals(self):
        """Shortcut to get sorted element values."""
        self.get_sorted_vals()

    @property
    def vals(self):
        """Shortcut to get unordered element values."""
        if self._elems is None:
            self._vals = self.elems.values()
        return self._vals

    @property
    def attrs(self):
        return self.get_elems(elem_type='attribute')

    @property
    def attr_vals(self):
        return self.get_vals(unordered=True, elem_type='attribute')

    @property
    def attr_svals(self):
        return self.get_vals(elem_type='attribute')

    @property
    def nodes(self):
        return self.get_elems(elem_type='node')

    @property
    def node_vals(self):
        return self.get_vals(unordered=True, elem_type='node')

    @property
    def node_svals(self):
        return self.get_vals(elem_type='node')

    def __iter__(self):
        return self

    def __next__(self):
        if self._i < self.len:
            i = self._i
            self._i += 1
            return self.vals[i]
        else:
            raise StopIteration

    next = __next__

    @property
    def len(self):
        if self._len is None:
            self._len = len(self.elems)
        return self._len

    def get_elem_by_name(self, name):
        try:
            return self.elems[name]
        except KeyError:
            raise ElemError(
                'element "%s" does not exist in this %s' % (
                    name, self.type.lower()))

    def get_elem_by_num(self, num, sort_by, unordered, elem_type):
        vals = self.get_vals(sort_by, unordered, elem_type)
        try:
            return vals[num - 1] if vals else None
        except IndexError:
            raise ElemError(
                'element index out of range (1-%d)' % len(vals))

    def get_elems(self, elem_type=None):
        """
        The generic method to get elements.

        :param elem_type: the element type.  If None, then all types are
                          included. Otherwise, it is one of "file",
                          "directory", "node", and "attribute".
        """
        elems = self.elems
        if elem_type is not None:
            items = self.elems.items()
            if elem_type not in ('file', 'directory', 'node', 'attribute'):
                raise NodeError('unknown element type')
            elem_class = getattr(sys.modules[__name__], elem_type.title())
            items = filter(lambda x: isinstance(x[1], elem_class), items)
            elems = OrderedDict(items)
        return elems

    def get_vals(self, sort_by=None, unordered=False, elem_type=None):
        """
        The generic method to get element values.

        :param sort_by: the name of the sorting key.  If it is None and
                        `unordered` is False, then the sorting key is the
                        element name.  If it is a name, then the content of the
                        attribute with this name is used as the key.
        :param unordered: whether to present elements unordered.  If it is
                          True, the original order in the document is used, and
                          `sort_by` has no effect.
        :param elem_type: the element type.  If None, then all types are
                          included. Otherwise, it is one of "file",
                          "directory", "node", and "attribute".
        """
        vals = self.vals
        if elem_type is not None:
            if elem_type not in ('file', 'directory', 'node', 'attribute'):
                raise NodeError('unknown element type')
            elem_class = getattr(sys.modules[__name__], elem_type.title())
            vals = filter(lambda elem: isinstance(elem, elem_class), vals)

        if unordered:
            return vals

        if sort_by is None:
            return sorted(vals, key=attrgetter('name'))

        def sort_key(elem):
            if getattr(elem, 'attrs'):
                return elem.attrs.get(sort_by)
            return None

        return sorted(self.vals, key=sort_key)

    def add(self, name, content):
        """
        Create an element with name and content and add it to this node.
        """
        if name not in self.elems:
            self.content[name] = content
            elem, this_is_dir, this_is_file = self._make_elem(name, content)
            self._elems[name] = elem
            self._update_class(this_is_dir, this_is_file)
            # update vals
            self._vals = self.elems.values()
        else:
            raise NodeError(
                'element "%s" already exists in this %s' % (
                    name, self.type.lower()))

    def delete(self, name):
        """Delete an element with name in this node."""
        if name in self.elems:
            this_is_dir, this_is_file = self._delete_elem(name)
            self._update_class(this_is_dir, this_is_file)
            # update vals
            self._vals = self.elems.values()
        else:
            raise NodeError(
                'element "%s" does not exist in this %s' % (
                    name, self.type.lower()))

    def _delete_elem(self, name):
        this_is_dir = self.is_dir
        this_is_file = self.is_file

        del self._elems[name]
        del self.content[name]

        if not self.content:
            # add a placeholder to keep this node as a file
            self.add(PLACEHOLDER, True)

        # check remaining elements
        for elem in self.elems:
            if self.elems[elem].is_attr:
                this_is_file = True
            if self.elems[elem].is_node:
                this_is_dir = True

        return this_is_dir, this_is_file


class ElemError(Exception):
    pass


class NodeError(Exception):
    pass


class AttrError(Exception):
    pass


class Directory(Node):
    pass


class File(Node):
    pass


class Attribute(Element):
    """
    The Attribute class.
    """
    def __init__(self, name, bucket, parent, content, *args, **kwargs):
        super(Attribute, self).__init__(name, bucket, parent, content,
                                        *args, **kwargs)
        self._action = AttributeAction(self)
        self._index = None
        self._decode_content()

    def _decode_content(self):
        if self.has_items:
            self.content = map(utf8_decode, self.content)
        else:
            self.content = utf8_decode(self.content)

    @property
    def is_item(self):
        return self._index is not None

    @property
    def has_items(self):
        return isinstance(self.content, list)

    def add(self, content):
        if not self.has_items:
            raise AttrError(
                'cannot add contents to non-list-type attribute')
        if isinstance(content, dict):
            raise AttrError(
                'cannot add dict-type content to list-type attribute')
        self.content.append(content)
