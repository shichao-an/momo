import os


from flask import Flask, send_from_directory, render_template, g
from flask_bootstrap import Bootstrap
from momo.settings import settings
from momo.plugins.flask import filters, functions
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


def get_root_node():
    return settings.bucket.root


@app.route('/node/<path:path>')
def node(path):
    nodes = []
    return render_template('node.html', nodes=nodes)


@app.route('/search')
def search():
    nodes = []
    return render_template('search.html', nodes=nodes)


@app.route('/')
def index():
    """Default index page that lists child nodes of root."""
    g.nodes = settings.bucket.root.node_vals
    return render_template('base.html')


@app.route('/files/<path:filename>')
def files(filename):
    """Get user files."""
    return send_from_directory(app.config['MOMO_FILES_FOLDER'], filename)
