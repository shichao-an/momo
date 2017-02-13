# template global functions
# make sure not to conflict with built-ins:
# http://jinja.pocoo.org/docs/2.9/templates/#list-of-global-functions


def attr(node, attr, default=None):
    """Get content of a node's attr. If attr is not present, return default."""
    if attr in node.attrs:
        return node.attrs[attr].content
    return default
