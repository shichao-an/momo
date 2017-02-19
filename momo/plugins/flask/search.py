# search backend
import re


from momo.plugins.flask.filters import get_attr
from momo.utils import txt_type


FALSE_STR_PATTREN = '^(0|false|False)$'


class SearchError(Exception):
    pass


def parse_search_term(term):
    """
    Parse a search term and returns list of lambdas lists.

    A search term is a path-like string seperated by slash (/). The slashes
    "AND" these path components together, meaning the results are those which
    satisfy all of them. Each component also comprises some sub-terms, in the
    form of "key1=value1&key2=value2", with each key having an optional
    prefix, which can be "n[x]:" (a node object's attribute) or "a[x]:" (an
    attr name); the optional "x" suffix indicates whether to perform an exact
    match. Note that although the sub-terms are seperated by ampersand (&),
    they are "OR"ed together, meaning the results are those satisfy any of
    them.

    """
    res = []
    entities = term.split('/')
    for entity in entities:
        subterms = filter(lambda x: x.strip(), entity.split('&'))
        lambdas = []
        for subterm in subterms:
            key, value = subterm.split('=')
            if ':' in key:
                prefix, name = key.split(':', 1)
                if prefix in ('a', 'ax'):
                    lambdas.append(
                        lambda node, name=name, value=value:
                        match_value(get_attr(node, name), value,
                                    prefix == 'ax')
                    )
                elif prefix in ('n', 'nx'):
                    lambdas.append(
                        lambda node, name=name, value=value:
                        match_value(getattr(node, name), value,
                                    prefix == 'nx')
                    )
                else:
                    raise SearchError('unknown prefix {}'.format(prefix))
            else:
                raise SearchError('no prefix specified')
        res.append(lambdas)
    return res


def match_value(value, s, exact=False):
    """
    Test whether the value of a node attribute or attr content matches the
    given string s, which is retrieved from parsed term.

    :param value: value of a node attribute or attr content.
    :param s: a string.
    :param exact: whether to do exact matches.
    """
    if value is None:
        return False
    s = txt_type(s)
    if isinstance(value, (txt_type, bool, int, float)):
        if isinstance(value, bool):
            return match_bool(value, s)
        else:
            if exact:
                return txt_type(value) == s
            else:
                return s in txt_type(value)
    else:
        txt_values = map(txt_type, value)
        if exact:
            return s in txt_values
        else:
            for txt_value in txt_values:
                if s in txt_value:
                    return True
            return False


def match_bool(value, s):
    """
    Test whether a boolean value matches the given string s.
    """
    if re.match(FALSE_STR_PATTREN, s):
        s = False
    else:
        s = True
    return value == s


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


def filter_default(node):
    """Default search filter function."""
    return True


def search_nodes(root, func=filter_default):
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
