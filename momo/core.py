# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from contextlib import contextmanager
from operator import attrgetter
from momo.utils import txt_type, PY3, utf8_decode
from momo.actions import NodeAction, AttributeAction
from momo.backends import OrderedDict
import sys


ROOT_NODE_NAME = '(root)'
INDENT_UNIT = '  '
LINES = []  # cached lines


@contextmanager
def lines(lines=None):
    if lines is None:
        global LINES
        lines = LINES
    try:
        yield lines
    finally:
        del lines[:]


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
        print(type(self._content))
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
    def __init__(self, name, bucket, parent, content, cache_lines=False,
                 no_output=False):
        """
        :param cache_lines: whether to cache lines to the global LINES
                            variable.
        :param no_output: whether to suppress output.
        """
        self.name = name
        self.bucket = bucket
        self.parent = parent
        self.content = content
        self.cache_lines = cache_lines
        self.no_output = no_output
        self._lines = []
        if parent is None:
            self.path = []
        else:
            self.path = parent.path[:]
            self.path.append(self.name)
        self._action = None

    @property
    def lines(self):
        if self.cache_lines:
            return LINES
        else:
            return self._lines

    def flush_lines(self):
        if self._lines:
            with lines(self._lines) as _lines:
                if not self.no_output:
                    print('\n'.join(_lines))

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
        this_is_dir = False
        this_is_file = False  # this will always be true
        is_dict = isinstance(content, dict)
        if not is_dict:
            this_is_file = True
            elem = (
                Attribute(name=name,
                          bucket=self.bucket,
                          parent=self,
                          content=content,
                          cache_lines=self.cache_lines,
                          no_output=self.no_output)
            )
        else:
            this_is_dir = True
            elem = Node(name=name,
                        bucket=self.bucket,
                        parent=self,
                        content=content,
                        cache_lines=self.cache_lines,
                        no_output=self.no_output)
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

    def ls(self, name_or_num=None, show_path=False, sort_by=None,
           unordered=False, elem_type=None, **kwargs):
        """
        List and print elements of the Node object.  If `name_or_num` is not
        None, then return the element that matches.

        :param name_or_num: element name or number.  The name has higher
                            precedence than number.
        :param show_path: whether to show path to the element.
        :param sort_by: the name of the sorting key.  If it is None, then the
                        sorting key is the element name.  If it is a name, then
                        the content of the attribute with this name is used as
                        the key.
        :param unordered: whether to present elements unordered.  If it is
                          True, the original order in the document is used.
        :param elem_type: the element type.  If None, then all types are
                          included. Otherwise, it is one of "file",
                          "directory", "node", and "attribute".

        :return: the element that matches `name_or_num` (if it is not None)
        """
        if show_path and not self.is_root:
            self._print_path()
        if name_or_num is None:
            self._ls_all(show_path, sort_by, unordered, elem_type)
        else:
            elem = None
            try:
                name_or_num = int(name_or_num)
            except ValueError:
                pass
            if isinstance(name_or_num, int):
                if str(name_or_num) in self.elems:
                    elem = self.get_elem_by_name(name_or_num)
                else:
                    elem = self.get_elem_by_num(
                        name_or_num, sort_by, unordered, elem_type)
            else:
                elem = self.get_elem_by_name(name_or_num)
            return elem

    def _ls_all(self, show_path, sort_by, unordered, elem_type):
        try:
            indent = ''
            if show_path:
                indent = INDENT_UNIT * self.level
            vals = self.get_vals(sort_by, unordered, elem_type)
            width = len(str(len(vals)))
            fmt = '%s%{}d [%s] %s'.format(width)
            for num, elem in enumerate(vals, start=1):
                self.lines.append(fmt % (indent, num, elem.type[0], elem))
        finally:
            self.flush_lines()

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
                'element "%s" does not exist in this % ' % (name, self.type))

    def get_elem_by_num(self, num, sort_by, unordered, elem_type):
        vals = self.get_vals(sort_by, unordered, elem_type)
        try:
            return vals[num - 1] if vals else None
        except IndexError:
            raise ElemError(
                'element index out of range (1-%d)' % len(vals))

    def _print_path(self):
        indent = INDENT_UNIT * (self.level - 1)
        self.lines.append('%s%s' % (indent, self.name))

    def get_elems(self, elem_type=None):
        """
        The generic method to get elements.

        :param elem_type: the element type.  If None, then all types are
                          included. Otherwise, it is one of "file",
                          "directory", "node", and "attribute".
        """
        elems = self.elems
        if elem_type is not None:
            elems = OrderedDict(self.elems)
            if elem_type not in ('file', 'directory', 'node', 'attribute'):
                raise NodeError('unknown element type')
            elem_class = getattr(sys.modules[__name__], elem_type.title())
            for elem in elems:
                if not isinstance(elems[elem], elem_class):
                    del elems[elem]
        return elems

    def get_vals(self, sort_by=None, unordered=False, elem_type=None):
        """
        The gneric method to get element values.

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
                'element "%s" already exists in this %s' % (name, self.type))


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

    def lsattr(self, name_or_num, show_path=False, expand_attr=False):
        """List attribute content."""
        try:
            if not self.has_items:
                raise AttrError('cannot list non-list-type attribute')
            indent = ''
            if show_path:
                indent = INDENT_UNIT * (self.level + 1)
            try:
                name_or_num = int(name_or_num)
            except ValueError:
                msg = 'must use a integer to index list-type attribute'
                raise AttrError(msg)
            content = self.content
            if expand_attr:
                content = self.parent.action.expand_attr(self.name)
            val = content[name_or_num - 1]
            self.lines.append(
                '%s%s[%d]: %s' % (indent, self.name, name_or_num, val))
            self._index = name_or_num
            return self
        finally:
            self.flush_lines()

    def ls(self, name_or_num=None, show_path=False, expand_attr=False,
           **kwargs):
        """
        List content of the attribute. If `name_or_num` is not None, return
        the matched item of the content.
        """
        if name_or_num is None:
            self._ls_all(show_path, expand_attr)
        else:
            return self.lsattr(name_or_num, show_path, expand_attr)

    def _ls_all(self, show_path, expand_attr):
        try:
            if self._index is not None:
                return
            indent = ''
            if show_path:
                indent = INDENT_UNIT * self.level
            content = self.content
            if expand_attr:
                content = self.parent.action.expand_attr(self.name)
            if self.has_items:
                self.lines.append('%s%s:' % (indent, self.name))
                indent += INDENT_UNIT
                width = len(str(len(content)))
                fmt = '%s%{}d %s'.format(width)
                for num, item in enumerate(content, start=1):
                    self.lines.append(fmt % (indent, num, item))
            elif isinstance(content, (txt_type, bool, int, float)):
                self.lines.append('%s%s: %s' % (indent, self.name, content))
            else:
                raise AttrError('unknown type for attribute content')
        finally:
            self.flush_lines()

    def add(self, content):
        if not self.has_items:
            raise AttrError(
                'cannot add contents to non-list-type attribute')
        if isinstance(content, dict):
            raise AttrError(
                'cannot add dict-type content to list-type attribute')
        self.content.append(content)
