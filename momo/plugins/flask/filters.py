# template filters
# make sure not to conflict with built-ins:
# http://jinja.pocoo.org/docs/2.9/templates/#builtin-filters


from momo.plugins.flask.functions import get_attr as _get_attr
from slugify import slugify as _slugify


def slugify(s):
    """Slugify a string."""
    return _slugify(s)


def attr_image(node):
    """Get image attr."""
    return _get_attr(node, 'image')


def attr_path(node):
    """Get path attr."""
    return _get_attr(node, 'path')


def node_to_path(node):
    """Get URL path (reverse of node_from_path)."""
    paths = []
    while node.parent is not None:
        paths.insert(0, node.name)
        node = node.parent
    return '/'.join(paths)
