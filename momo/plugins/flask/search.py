# search backend
from momo.plugins.flask.filters import get_attr
from momo.utils import txt_type


class SearchError(Exception):
    pass


def parse_search_term(term):
    """Parse a search term and returns list of list of lambdas."""
    res = []
    entities = term.split('/')
    for entity in entities:
        subterms = filter(lambda x: x.strip(), entity.split('&'))
        lambdas = []
        for subterm in subterms:
            key, value = subterm.split('=')
            if ':' in key:
                prefix, name = key.split(':', 1)
                if prefix == 'a':
                    lambdas.append(
                        lambda node, name=name, value=value:
                        txt_type(get_attr(node, name)) == value
                    )
                elif prefix == 'n':
                    lambdas.append(
                        lambda node, name=name, value=value:
                        txt_type(getattr(node, name)) == value
                    )
                else:
                    raise SearchError('unknown prefix {}'.format(prefix))
            else:
                raise SearchError('no prefix specified')
        res.append(lambdas)
    return res


def match_content(content, s, exact=False):
    """
    Test whether the value of node attribute or attr content matches the
    give string s, which is retrieved from parsed term.

    :param content:
    """
    if isinstance(content, (txt_type, bool, int, float)):
        pass
    else:
        pass


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
