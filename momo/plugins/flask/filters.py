# template filters
# make sure not to conflict with built-ins:
# http://jinja.pocoo.org/docs/2.9/templates/#builtin-filters


from momo.plugins.flask.globals import attr as _attr
from slugify import slugify as _slugify


def slugify(s):
    """Slugify a string."""
    return _slugify(s)


def image(node):
    """Get image of a node."""
    return _attr(node, 'image')


def path(node):
    """Get path of a node."""
    return _attr(node, 'path')
