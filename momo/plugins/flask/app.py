import os

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from flask_bootstrap import Bootstrap
from momo.plugins.flask import filters, functions
import momo.plugins.flask.nodes
from momo.plugins.flask.utils import get_public_functions


FLASK_DEFAULT_HOST = '127.0.0.1'
FLASK_DEFAULT_PORT = '7000'
FLASK_DEFAULT_DEBUG = True
FLASK_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
FLASK_TEMPLATE_FOLDER = os.path.join(FLASK_APP_ROOT, 'templates')
FLASK_STATIC_FOLDER = os.path.join(FLASK_APP_ROOT, 'static')

app = Flask(
    import_name=__name__,
    template_folder=FLASK_TEMPLATE_FOLDER,
    static_folder=FLASK_STATIC_FOLDER,
)

# instrument app
Bootstrap(app)

# extensions
app.jinja_env.add_extension('jinja2.ext.do')

# register default filters
app.jinja_env.filters.update(get_public_functions(filters))

# register default global functions
app.jinja_env.globals.update(get_public_functions(functions))

app.url_map.strict_slashes = False

"""
Query strings for all views:

    ?sort=: sort by a key, which can be prefixed with a: (attr), n: (node
    object attribute), and f: (a pre-defined function).
    ?desc=: in descending order (only effective when ?sort= is present)

"""


def get_node_function(name, functions):
    if name in functions:
        return functions[name]
    else:
        return getattr(momo.plugins.flask.nodes, name)


@app.route('/node')
@app.route('/node/<path:path>')
def node(path=None):
    if path is None:
        return redirect('/')

    root = app.config['MOMO_ROOT_NODE']
    funcs = app.config['MOMO_NODES_FUNCTIONS']

    get_node_function('pre_node', funcs)(
        path=path,
        root=root,
        request=request)

    node = get_node_function('process_node', funcs)(
        path=path,
        root=root,
        request=request,
    )

    node = get_node_function('post_node', funcs)(
        path=path,
        root=root,
        request=request,
        node=node,
    )

    return render_template('node.html', node=node)


@app.route('/search')
@app.route('/search/<path:term>')
def search(term=None):
    """
    A search term is a path-like string seperated by slash (/). The slashes
    "AND" these path components together, meaning the results are those which
    satisfy all of them. Each component also comprises some sub-terms, in the
    form of "key1=value1&key2=value2", with each key having an optional
    prefix, which can be "n:" (a node object's attribute) or "a:" (an attr
    name); if the prefix is omitted, then it defaults to "a:". Note that
    although the sub-terms are seperated by ampersand (&), they are "OR"ed
    together, meaning the results are those satisfy any of them.

    Query string is "?q=", which indicates a query that is used to match
    content of all attrs of all nodes all filtered in the above steps.
    """

    root = app.config['MOMO_ROOT_NODE']
    funcs = app.config['MOMO_NODES_FUNCTIONS']

    get_node_function('pre_search', funcs)(
        root=root,
        term=term,
        request=request,
    )

    nodes = get_node_function('process_search', funcs)(
        root=root,
        term=term,
        request=request,
    )

    nodes = get_node_function('post_search', funcs)(
        root=root,
        term=term,
        request=request,
        nodes=nodes,
    )

    return render_template('search.html', nodes=nodes)


@app.route('/')
def index():
    """
    Default index page that lists all nodes of root, deemed as a special
    case for /node/.
    """

    root = app.config['MOMO_ROOT_NODE']
    funcs = app.config['MOMO_NODES_FUNCTIONS']

    get_node_function('pre_index', funcs)(
        root=root,
        request=request
    )

    nodes = get_node_function('process_index', funcs)(
        root=root,
        request=request,
    )

    nodes = get_node_function('post_index', funcs)(
        root=root,
        request=request,
        nodes=nodes,
    )

    return render_template('index.html', nodes=nodes)


@app.route('/files/<path:filename>')
def files(filename):
    """Get user files."""
    return send_from_directory(app.config['MOMO_FILES_FOLDER'], filename)


@app.before_request
def fix_trailing():
    """Always add a single trailing slash."""
    rp = request.path
    if rp != '/':
        if not rp.endswith('/'):
            return redirect(rp + '/')
        elif rp.endswith('//'):
            return redirect(rp.rstrip('/') + '/')
