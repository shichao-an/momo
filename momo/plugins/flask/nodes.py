# functions to process nodes
import os
from flask import g
from momo.plugins.flask.search import (
    parse_search_term, search_nodes, get_search_filter)


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
        parsed_term = parse_search_term(term)
        search_filter = get_search_filter(parsed_term)
        nodes = search_nodes(root, search_filter)
    else:
        nodes = root.node_vals
    return nodes


def post_search(root, term, request, nodes):
    """
    Function to post-process requests for search view. It is used to
    post-process the nodes.
    """
    nodes = sort_nodes(nodes, func=lambda node: node.name)
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
    return nodes


def node_from_path(path, root):
    node = root
    for name in path.split('/'):
        node = node.elems[name]
    return node


def sort_nodes(nodes, func, desc=False):
    """
    Sort nodes in-place.

    :param nodes: list of nodes.
    :param func: a function that returns an item as sorting key.
    :param desc: whether in descending order.
    """
    nodes.sort(key=func, reverse=desc)
    return nodes
