# template filters
# make sure not to conflict with built-ins:
# http://jinja.pocoo.org/docs/2.9/templates/#builtin-filters

from slugify import slugify as _slugify


def get_attr(node, attrname, default=None):
    """Get content of a node's attr. If attr is not present, return default."""
    if attrname in node.attrs:
        return node.attrs[attrname].content
    return default


def slugify(s):
    """Slugify a string."""
    return _slugify(s)


def attr_image(node):
    """Shortcut to get_attr(node, 'image')."""
    return get_attr(node, 'image')


def attr_path(node):
    """Shortcut to get_attr(node, 'path')."""
    return get_attr(node, 'path')


def node_to_path(node):
    """Get URL path from a node (reverse of node_from_path)."""
    paths = []
    while node.parent is not None:
        paths.insert(0, node.name)
        node = node.parent
    return '/'.join(paths)


def split_path(path):
    """Split a path into a list of path components."""
    return path.split('/')


def sort_attrs(attrs):
    """Placeholder overriden by app.config['MOMO_ATTRS_SORTING']."""


def pin_attrs(attrs):
    """Placeholder overriden by app.config['MOMO_ATTRS_PINNING']."""
