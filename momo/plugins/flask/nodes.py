# functions to process nodes
from collections import OrderedDict
from flask import g
from momo.plugins.flask.search import (
    search_nodes_by_term,
    parse_q,
    join_terms
)


def pre_node(path, root, request):
    """
    Function to pre-process requests for node view. It is used to update g.
    """
    pass


def process_node(path, root, request):
    """
    Function to process requests for node view. It generates and returns a
    node.
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
    pass


def process_search(root, term, request):
    """
    Function to process requests for search view. It generates and returns
    nodes.
    """
    q = request.args.get('q')
    if q:
        if term:
            term = join_terms(term, parse_q(q))
        else:
            term = parse_q(q)
    g.permalink = '/search/'
    if term:
        g.permalink += term
        nodes = search_nodes_by_term(term, root, g.case_insensitive)
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
    pass


def process_index(root, request):
    """
    Function to process requests for index view. It generates and returns
    nodes.
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


def merge_nodes(nodes):
    """
    Merge nodes to deduplicate same-name nodes and add a "parents"
    attribute to each node, which is a list of Node objects.
    """

    def add_parent(unique_node, parent):
        if getattr(unique_node, 'parents', None):
            if parent.name not in unique_node.parents:
                unique_node.parents[parent.name] = parent
        else:
            unique_node.parents = {parent.name: parent}

    names = OrderedDict()
    for node in nodes:
        if node.name not in names:
            names[node.name] = node
            add_parent(names[node.name], node.parent)
        else:
            add_parent(names[node.name], node.parent)
    return names.values()
