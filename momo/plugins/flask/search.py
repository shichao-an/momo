# search backend

from momo.plugins.flask.filters import get_attr
from momo.plugins.flask.utils import str_to_bool
from momo.utils import txt_type, bin_type


class SearchError(Exception):
    pass


def join_terms(*args):
    res = []
    for arg in args:
        res.append(arg.strip('/'))
    return '/'.join(res)


def parse_q(s):
    """Parse the value of query string q (?q=) into a search sub-term."""
    if '=' not in s:
        names = s.split()
        term = '&'.join(map(lambda x: 'n.name=' + x, names))
        return term
    else:
        subterms = s.split()
        res = []
        for subterm in subterms:
            if '=' not in subterm:
                res.append('n.name=' + subterm)
            else:
                res.append(subterm)
        term = '&'.join(res)
        return term


def search_nodes_by_term(term, root, case_insensitive):
    """
    High-level function to search nodes by search term. It does three things:

    1. Parse the search term into a list of lambda lists.
    2. Generate a search filter function.
    3. Search the nodes with the search filter function.

    """
    parsed_term = parse_search_term(term, case_insensitive)
    search_filter = get_search_filter(parsed_term)
    nodes = search_nodes(root, search_filter)
    return nodes


def parse_search_term(term, case_insensitive=False):
    """
    Parse a search term and returns a list of lambdas lists.

    A search term is a path-like string seperated by slash (/). The slashes
    "AND" these path components together, meaning the results are those which
    satisfy all of them. Each component also comprises some sub-terms, in the
    form of "key1=value1&key2=value2", with each key having an optional
    prefix, which can be "n[x_]." (a node object's attribute) or "a[x]." (an
    attr name); the optional "x" suffix indicates whether to perform an exact
    match and "_" suffix indicates that to match nodes without this node
    object attribute or attr. Note that although the sub-terms are seperated
    by ampersand (&), they are "OR"ed together, meaning the results are those
    satisfy any of them.

    """
    res = []
    entities = term.split('/')
    for entity in entities:
        subterms = filter(lambda x: x.strip(), entity.split('&'))
        lambdas = []
        for subterm in subterms:
            key, s = subterm.split('=')
            if '.' in key:
                prefix, name = key.split('.', 1)
                if prefix in ('a', 'ax', 'a_'):
                    lambdas.append(
                        lambda node, name=name, s=s, prefix=prefix:
                        match_value(
                            value=get_attr(node, name),
                            s=s,
                            exact=prefix == 'ax',
                            without=prefix == 'a_',
                            case_insensitive=case_insensitive,
                        )
                    )
                elif prefix in ('n', 'nx', 'n_'):
                    lambdas.append(
                        lambda node, name=name, s=s, prefix=prefix:
                        match_value(
                            value=getattr(node, name, None),
                            s=s,
                            exact=prefix == 'nx',
                            without=prefix == 'n_',
                            case_insensitive=case_insensitive,
                        )
                    )
                else:
                    raise SearchError('unknown prefix {}'.format(prefix))
            else:
                raise SearchError('no prefix specified')
        if lambdas:
            res.append(lambdas)
    return res


def match_value(value, s, exact=False, without=False, case_insensitive=False):
    """
    Test whether the value of a node attribute or attr content matches the
    given string s, which is retrieved from parsed term.

    :param value: value of a node attribute or attr content.
    :param s: a string.
    :param exact: whether to do exact matches.
    :param without: if True, match if value is None (meaning value does not
                    exist in the node).
    """

    def with_case(a):
        if case_insensitive:
            return a.lower()
        else:
            return a

    if value is None:
        if without:
            return True
        else:
            return False
    else:
        if without:
            return False
    s = txt_type(s)
    if isinstance(value, (txt_type, bin_type, bool, int, float)):
        if isinstance(value, bool):
            return match_bool(value, s)
        else:
            if exact:
                return with_case(txt_type(value)) == (s)
            else:
                return with_case(s) in with_case(txt_type(value))
    else:
        txt_values = map(with_case, map(txt_type, value))
        if exact:
            return with_case(s) in txt_values
        else:
            for txt_value in txt_values:
                if with_case(s) in with_case(txt_value):
                    return True
            return False


def match_bool(value, s):
    """
    Test whether a boolean value matches the given string s.
    """
    return value == str_to_bool(s)


def get_search_filter(lambda_lists):
    """Generate a search filter based on the lambda lists."""
    def search_filter(node):
        """Evaluate node and reduce lambda_lists."""
        evaluated_list = [
            reduce(lambda x, y: x or y, map(lambda x: x(node), lambda_list))
            for lambda_list in lambda_lists
        ]
        return reduce(lambda x, y: x and y, evaluated_list)
    return search_filter


def search_nodes(root, func=lambda x: True):
    """
    Search nodes from the root in a BFS manner.

    :param root: the root node.
    :param func: a filtering function.
    """

    nodes = []
    queue = [root]
    while queue:
        cur_node = queue.pop(0)
        for node in cur_node.node_vals:
            if func(node):
                nodes.append(node)
            queue.append(node)
    return nodes
