# functions to process nodes
import os
from flask import g
from momo.plugins.flask.search import search_nodes_by_term
from momo.plugins.flask.sorting import sort_nodes_by_terms
from momo.plugins.flask.utils import str_to_bool


def pre_node(path, root, request):
    """
    Function to pre-process requests for node view. It is used to update g.
    """
    g.path = path
    g.title = os.path.basename(path)


def process_node(path, root, request):
    """
    Function to process requests for node view. It returns a node.
    """
    node = node_from_path(path, root)
    return node


def post_node(path, root, request, node):
    """
    Function to post-process requests for node view. It is used to
    post-process the node.
    """
    return node


def pre_search(root, term, request):
    """
    Function to pre-process requests for search view. It is used to update g.
    """
    g.title = 'Search'


def process_search(root, term, request):
    """
    Function to process requests for search view. It returns nodes.
    """
    if term is not None:
        nodes = search_nodes_by_term(term, root)
    else:
        nodes = root.node_vals
    return nodes


def post_search(root, term, request, nodes):
    """
    Function to post-process requests for search view. It is used to
    post-process the nodes.
    """
    return nodes


def pre_index(root, request):
    """
    Function to pre-process requests for index view. It updates g.
    """
    g.title = 'Index'


def process_index(root, request):
    """
    Function to process requests for index view. It returns nodes.
    """
    nodes = root.node_vals
    return nodes


def post_index(root, request, nodes):
    """
    Function to post-process requests for index view. It is used to
    post-process the nodes.
    """
    sorting_terms = request.args.getlist('sort')
    desc = request.args.get('desc', default=False, type=str_to_bool)
    sort_nodes_by_terms(
        terms=sorting_terms,
        nodes=nodes,
        desc=desc,
        functions=g.sorting_functions,
    )
    return nodes


def node_from_path(path, root):
    node = root
    for name in path.split('/'):
        node = node.elems[name]
    return node
