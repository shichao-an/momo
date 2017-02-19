# sorting key functions


def sort_by_numnode(node):
    """
    Sort by number of node.
    """
    return len(node.nodes)


def sort_by_numattr(node):
    """
    Sort by number of attrs.
    """
    return len(node.attrs)


def sort_by_numelem(node):
    """
    Sort by number of elements.
    """
    return len(node.elems)
