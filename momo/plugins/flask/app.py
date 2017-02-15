import os

from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from flask_bootstrap import Bootstrap
from flask_paginate import Pagination
from momo.plugins.flask import filters, functions
from momo.plugins.flask.nodes import process_node
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


def paginate(page, total, per_page, config):
    record_name = config['MOMO_PAGINATION_RECORD_NAME']
    display_msg = config['MOMO_PAGINATION_DISPLAY_MSG']
    pagination = _paginate(
        page=page,
        total=total,
        per_page=per_page,
        record_name=record_name,
        display_msg=display_msg,
    )
    return pagination


def _paginate(page, total, per_page, record_name, display_msg):
    pagination = Pagination(
        page=page,
        total=total,
        bs_version=3,
        show_single_page=False,
        record_name=record_name,
        display_msg=display_msg,
    )
    return pagination


@app.route('/node')
@app.route('/node/<path:path>')
def node(path=None):
    if path is None:
        return redirect('/')
    g.path = path
    g.title = os.path.basename(path)
    node = process_node(path, app.config['MOMO_ROOT_NODE'], request)
    return render_template('node.html', node=node)


@app.route('/search')
def search():
    g.title = 'Search'
    g.active_page = 'search'
    nodes = []
    return render_template('search.html', nodes=nodes)


@app.route('/')
def index():
    """
    Default index page that lists all nodes of root, deemed as a special
    case for /node/.
    """
    g.title = 'Index'
    g.active_page = 'index'

    nodes = app.config['MOMO_ROOT_NODE'].node_vals
    page = request.args.get('page', type=int, default=1)
    per_page = app.config['MOMO_PAGINATION_INDEX_PER_PAGE']
    g.nodes = nodes[per_page * (page - 1):per_page * page]
    g.pagination = paginate(
        page=page, total=len(nodes), per_page=per_page, config=app.config)

    return render_template('index.html')


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
