# template global functions
# make sure not to conflict with built-ins:
# http://jinja.pocoo.org/docs/2.9/templates/#list-of-global-functions


def get_attr(node, attrname, default=None):
    """Get content of a node's attr. If attr is not present, return default."""
    if attrname in node.attrs:
        return node.attrs[attrname].content
    return default
