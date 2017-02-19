# sorting and sorting key functions

from momo.plugins.flask.filters import get_attr


class SortingError(Exception):
    pass


def sort_nodes_by_terms(terms, nodes, desc, functions):
    """
    High-level function to sort by a sorting term. It does two things:

    1. Parse the sorting terms into a list of sorting key functions.
    2. Apply sorting nodes in-place with the sorting key functions in turn.
    """
    funcs = parse_sorting_terms(terms, functions)
    for func in funcs:
        sort_nodes(nodes, func, desc)
    return nodes


def sort_nodes(nodes, func, desc=False):
    """
    Sort nodes in-place.

    :param nodes: list of nodes.
    :param func: a function that returns an item as sorting key.
    :param desc: whether in descending order.
    """
    nodes.sort(key=func, reverse=desc)
    return nodes


def parse_sorting_terms(terms, functions):
    """
    Parse a list of sorting terms into a list of sorting key functions.

    :param terms: a list of sorting terms.
    :param functions: a dictionary of sorting key functions.
    """
    res = []
    for term in terms:
        prefix, name = term.split('.')
        if prefix == 'a':
            res.append(lambda node, name=name: get_attr(node, name))
        elif prefix == 'n':
            res.append(lambda node, name=name: getattr(node, name))
        elif prefix == 'f':
            func_name = 'sort_by_' + name
            res.append(lambda node, name=func_name: functions[name])
        else:
            raise SortingError('unknown sorting prefix')
    return res


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
