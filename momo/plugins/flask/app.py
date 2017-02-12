import os
from flask import Flask

FLASK_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
FLASK_TEMPLATE_FOLDER = os.path.join(FLASK_APP_ROOT, 'templates')
FLASK_STATIC_FOLDER = os.path.join(FLASK_APP_ROOT, 'static')

app = Flask(
    import_name=__name__,
    template_folder=FLASK_TEMPLATE_FOLDER,
    static_folder=FLASK_STATIC_FOLDER,
)


@app.route('/node/<path:path>')
def node(path):
    return path


@app.route('/search')
def search():
    return 'Search Page'


@app.route('/')
def index():
    return 'Index Page'
