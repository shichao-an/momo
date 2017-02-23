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
from momo.plugins.flask.utils import get_public_functions, to_list
import momo.plugins.flask.sorting
import momo.plugins.flask.nodes
from momo.plugins.flask.sorting import sort_nodes

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
MOMO_ATTRS_SORTING: the default sorting function of node attrs. It is
                    registered as a template filter as "sort_attrs".
MOMO_NODES_SORTING: the default sorting function of nodes.
MOMO_ATTRS_PINNING: the function to pin selected attrs to the top.
MOMO_VIEW: default view, which can be "list" (default), "table", or any other
           user-defined templates prefixed with "view_".
MOMO_VIEW_INDEX: default view for the index view function.
MOMO_VIEW_SEARCH: default view for the search view function.
MOMO_VIEW_NODE: default view for the node view function.
MOMO_ROOT_REVERSED: use reversed order for listing root nodes (latest first).
MOMO_MERGE_NODES: whether to merge nodes with the same name (search view
                  only).
MOMO_CASE_INSENSITIVE: whether to use case insensitive matching for search.
MOMO_INDEX_SORTING_TERMS: the default sorting term for index view.
MOMO_SEARCH_SORTING_TERMS: the default sorting term for search view.
MOMO_NODE_SORTING_TERMS: the default sorting term for node view.
MOMO_HOLDER_SIZE: holder (image placeholder) size (in the form of NxM).
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
        # TODO: refactor these code
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
        app.config['MOMO_PAGINATION_SEARCH_PER_PAGE'] = self.configs.get(
            'pagination_search_per_page', 20)
        app.config['MOMO_PAGINATION_DISPLAY_MSG'] = self.configs.get(
            'pagination_display_msg', '{total} {record_name}s.')
        app.config['MOMO_PAGINATION_NODE_PER_PAGE'] = self.configs.get(
            'pagination_node_per_page', 20)

        app.config['MOMO_VIEW'] = self.configs.get('view', 'list')
        app.config['MOMO_VIEW_INDEX'] = self.configs.get('view_index')
        app.config['MOMO_VIEW_SEARCH'] = self.configs.get('view_search')
        app.config['MOMO_VIEW_NODE'] = self.configs.get('view_node')
        app.config['MOMO_ROOT_REVERSED'] = self.configs.get('root_reversed')
        app.config['MOMO_MERGE_NODES'] = self.configs.get('merge_nodes')
        app.config['MOMO_CASE_INSENSITIVE'] = self.configs.get(
            'case_insensitive', False)
        app.config['MOMO_HOLDER_SIZE'] = self.configs.get(
            'holder_size', '125x125')

        index_sorting_terms = self.configs.get('index_sorting_terms')
        app.config['MOMO_INDEX_SORTING_TERMS'] = (
            to_list(index_sorting_terms) if index_sorting_terms else None)
        search_sorting_terms = self.configs.get('search_sorting_terms')
        app.config['MOMO_SEARCH_SORTING_TERMS'] = (
            to_list(search_sorting_terms) if search_sorting_terms else None)
        node_sorting_terms = self.configs.get('node_sorting_terms')
        app.config['MOMO_NODE_SORTING_TERMS'] = (
            to_list(node_sorting_terms) if node_sorting_terms else None)

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

        # initialize default sorting function for attrs
        sort_attrs_asc = self.configs.get('sort_attrs_asc')
        app.config['MOMO_ATTRS_SORTING'] = lambda attrs: attrs
        if sort_attrs_asc is not None:
            app.config['MOMO_ATTRS_SORTING'] = \
                lambda attrs: sorted(
                    attrs,
                    key=lambda attr: attr.name,
                    reverse=not sort_attrs_asc,
                )
        app.jinja_env.filters.update(
            sort_attrs=app.config['MOMO_ATTRS_SORTING'])

        # initialize default sorting function for nodes
        sort_nodes_asc = self.configs.get('sort_nodes_asc')
        app.config['MOMO_NODES_SORTING'] = lambda nodes: nodes
        if sort_nodes_asc is not None:
            app.config['MOMO_NODES_SORTING'] = \
                lambda nodes: sort_nodes(
                    nodes,
                    func=lambda node: node.name,
                    desc=not sort_nodes_asc,
                )

        # initialize pinning (reordering) function for attrs
        pinned_attrs = self.configs.get('pinned_attrs') or []
        app.config['MOMO_ATTRS_PINNING'] = \
            self._get_pinning_function(pinned_attrs)
        app.jinja_env.filters.update(
            pin_attrs=app.config['MOMO_ATTRS_PINNING'])

        # load system and user-define sorting key functions
        app.config['MOMO_SORTING_FUNCTIONS'] = self._load_functions(
            module=momo.plugins.flask.sorting,
            filename=os.path.join(flask_dir, 'sorting.py'),
            prefix='sort_by_',
        )

    def _get_pinning_function(self, pinned_attrs):
        """Return a (template filter) function that reorders attrs based on
        the given piined attrs."""

        def pin_attrs(attrs):
            pinned = []
            others = []
            for attr in attrs:
                if attr.name in pinned_attrs:
                    pinned.append(attr)
                else:
                    others.append(attr)
            return pinned + others

        return pin_attrs

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
