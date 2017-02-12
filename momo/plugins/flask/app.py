import os
import re
import unicodedata
from flask import Flask, send_from_directory, render_template
from flask_bootstrap import Bootstrap
from momo.settings import settings


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
app.jinja_env.add_extension('jinja2.ext.do')


def get_root_node():
    return settings.bucket.root


# filters
@app.template_filter('slugify')
def slugify(s):
    s = unicode(s)
    separator = '-'
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    s = re.sub('[^\w\s-]', '', s.decode('ascii')).strip().lower()
    return re.sub('[%s\s]+' % separator, separator, s)


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
    nodes = get_root_node().node_vals
    return render_template(
        'base.html', nodes=nodes, title=app.config['MOMO_SITENAME'])


@app.route('/files/<path:filename>')
def files(filename):
    """Get user files."""
    return send_from_directory(app.config['MOMO_FILES_FOLDER'], filename)
