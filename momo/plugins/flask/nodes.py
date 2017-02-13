# functions to process nodes


def process_node(path, root, request):
    """
    Function to process requests for node view.
    """
    node = node_from_path(root)
    return node


def process_search(root, request):
    """
    Function to process requests for search view.
    """
    pass


def node_from_path(path, root):
    node = root
    for name in path.split('/'):
        node = root.elems[name]
    return node
