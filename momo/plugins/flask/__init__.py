import imp
import os
import jinja2
from momo.plugins.base import Plugin
from momo.plugins.flask.app import (
    app,
    FLASK_TEMPLATE_FOLDER,
    FLASK_DEFAULT_HOST,
    FLASK_DEFAULT_PORT,
    FLASK_DEFAULT_DEBUG
)
from momo.plugins.flask.utils import get_public_functions
import momo.plugins.flask.sorting
import momo.plugins.flask.nodes

"""
app.config values of the current bucket:

MOMO_ROOT_NODE: the root node of the current bucket.
MOMO_FILES_FOLDER: user files folder.
MOMO_SITENAME: sitename (defaults to bucket name).
MOMO_HEADER_ID: what to show in the header id attribute of the node, which can
                be false (do not show id, default), slug (slugify the header
                text), or true (use the header text, which may break browser
                javascripts if containing invalid characters).
MOMO_TOC_HEADER: whether to include main header in the TOC (defaults to true).
MOMO_INDEX_TABLE: whether to use table format in the index page (defaults to
                  false).
MOMO_PAGINATION_RECORD_NAME: record name for pagination (defaults to 'node').
MOMO_PAGINATION_INDEX_PER_PAGE: per page number for index page (default 20).
MOMO_PAGINATION_NODE_PER_PAGE: per page number for node page (default 20).
MOMO_PAGINATION_DISPLAY_MSG: display message for pagination (defaults to
                             '{total} {record_name}.')
MOMO_NODES_FUNCTIONS: a dictionary of names to default and user node functions
                      (see nodes.py).
MOMO_SORTING_FUNCTIONS: a dictionary of names to default and user sorting key
                        functions (see sorting.py).
MOMO_NODE_ATTRS_SORTED: whether to sort the node attrs by name.
MOMO_NODE_NODES_SORTED: whether to sort the node's child nodes by name.
"""


class Flask(Plugin):
    def setup(self):
        bucket_name = self.settings.bucket.name
        self.configs = self.settings.plugins.get(
            'flask', {}).get(bucket_name, {})
        flask_dir = os.path.join(
            self.settings.settings_dir, 'flask', bucket_name)

        # register user template folder
        user_template_folder = os.path.join(flask_dir, 'templates')
        self._reset_loader(user_template_folder)

        # configuration values
        app.config['MOMO_ROOT_NODE'] = self.settings.bucket.root
        app.config['MOMO_FILES_FOLDER'] = os.path.join(flask_dir, 'files')
        app.config['MOMO_SITENAME'] = (
            self.configs.get('sitename') or bucket_name.capitalize())
        app.config['MOMO_HEADER_ID'] = self.configs.get('header_id', False)
        app.config['MOMO_TOC_HEADER'] = self.configs.get('toc_title', True)
        app.config['MOMO_INDEX_TABLE'] = self.configs.get('index_table', False)

        app.config['MOMO_PAGINATION_RECORD_NAME'] = self.configs.get(
            'pagination_record_name', 'node')
        app.config['MOMO_PAGINATION_INDEX_PER_PAGE'] = self.configs.get(
            'pagination_index_per_page', 20)
        app.config['MOMO_PAGINATION_NODE_PER_PAGE'] = self.configs.get(
            'pagination_node_per_page', 20)
        app.config['MOMO_PAGINATION_DISPLAY_MSG'] = self.configs.get(
            'pagination_display_msg', '{total} {record_name}s.')

        # load and register user-defined filter and global functions
        filters_f = os.path.join(flask_dir, 'filters.py')
        if os.path.isfile(filters_f):
            filters = imp.load_source('filters', filters_f)
            app.jinja_env.filters.update(get_public_functions(filters))

        functions_f = os.path.join(flask_dir, 'functions.py')
        if os.path.isfile(functions_f):
            functions = imp.load_source('functions', functions_f)
            app.jinja_env.globals.update(get_public_functions(functions))

        # load system and user-defined nodes functions
        app.config['MOMO_NODES_FUNCTIONS'] = self._load_functions(
            module=momo.plugins.flask.nodes,
            filename=os.path.join(flask_dir, 'nodes.py'),
        )

        # load system and user-define sorting key functions
        app.config['MOMO_SORTING_FUNCTIONS'] = self._load_functions(
            module=momo.plugins.flask.sorting,
            filename=os.path.join(flask_dir, 'sorting.py'),
            prefix='sort_by_',
        )

    def _load_functions(self, module, filename, prefix=''):
        """Load functions from a module and a user file. The functions from
        latter are able to override the those from the former. If the user
        file does not exist, then ignore loading functions from it.
        """
        # default function
        functions = {
            name: func for (name, func) in
            get_public_functions(module).items()
            if name.startswith(prefix)
        }
        if os.path.isfile(filename):
            user_mod = imp.load_source('', filename)
            user_funcs = get_public_functions(user_mod)
            functions.update({
                name: func for (name, func) in user_funcs.items()
                if name.startswith(prefix)
            })
        return functions

    def _reset_loader(self, user_template_folder):
        """Add user-defined template folder."""
        app.jinja_loader = jinja2.FileSystemLoader([
            user_template_folder,
            FLASK_TEMPLATE_FOLDER,
        ])

    def run(self, args=None):
        # args is not used for now
        host = self.configs.get('host') or FLASK_DEFAULT_HOST
        port = self.configs.get('port') or FLASK_DEFAULT_PORT
        debug = self.configs.get('debug') or FLASK_DEFAULT_DEBUG

        print('Serving on http://{}:{}...'.format(host, port))

        app.run(
            host=host,
            port=port,
            debug=debug,
        )

plugin = Flask()
