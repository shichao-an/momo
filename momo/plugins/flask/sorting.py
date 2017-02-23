# sorting and sorting key functions

from momo.plugins.flask.filters import get_attr
from momo.plugins.flask.utils import str_to_bool


class SortingError(Exception):
    pass


def sort_nodes_by_request(nodes, request, g, default_reverse=False,
                          default_terms=None):
    """High-level function to sort nodes with a request object."""
    sorting_terms = request.args.getlist('sort') or default_terms
    desc = request.args.get('desc', default=False, type=str_to_bool)
    if not sorting_terms:
        if desc:
            nodes.reverse()
        elif default_reverse:
            nodes.reverse()
    else:
        nodes = sort_nodes_by_terms(
            terms=sorting_terms,
            nodes=nodes,
            desc=desc,
            functions=g.sorting_functions,
        )
    return nodes


def sort_nodes_by_terms(terms, nodes, desc, functions):
    """
    High-level function to sort nodes by sorting term. It does two things:

    1. Parse the sorting terms into a list of sorting key functions.
    2. Combine the sorting key functions into a single lambda function.
    3. Apply sorting nodes in-place with the combined lambda function.
    """
    funcs = parse_sorting_terms(terms, functions)
    sort_nodes(nodes, lambda node: [func(node) for func in funcs], desc)
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
            res.append(lambda node, name=name: getattr(node, name, None))
        elif prefix == 'f':
            name = 'sort_by_' + name
            res.append(functions[name])
        else:
            raise SortingError('unknown sorting prefix')
    return res


def sort_by_numnodes(node):
    """
    Sort by number of nodes.
    """
    return len(node.nodes)


def sort_by_numattrs(node):
    """
    Sort by number of attrs.
    """
    return len(node.attrs)


def sort_by_numelems(node):
    """
    Sort by number of elements.
    """
    return len(node.elems)
