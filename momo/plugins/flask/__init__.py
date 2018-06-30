from __future__ import print_function, absolute_import
import imp
import os
import sys
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

from gevent.wsgi import WSGIServer

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
MOMO_HEADER_NODE_COUNT: whether to include node count in the node header.
MOMO_HEADER_NODE_COUNT_LEVELS: the node levels to which the count is included.
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
MOMO_LIST_NODE_ATTRS: whether to list node attrs in applicable views, such as
                      the "list" view (defaults to True).
MOMO_ROOT_REVERSED: use reversed order for listing root nodes (latest first).
MOMO_MERGE_NODES: whether to merge nodes with the same name (search view
                  only).
MOMO_CASE_INSENSITIVE: whether to use case insensitive matching for search.
MOMO_STRING_SEPARATOR: string separator used when matching nodes for search.
MOMO_INDEX_SORTING_TERMS: the default sorting term for index view.
MOMO_SEARCH_SORTING_TERMS: the default sorting term for search view.
MOMO_NODE_SORTING_TERMS: the default sorting term for node view.
MOMO_HOLDER_SIZE: holder (image placeholder) size (in the form of NxM).
MOMO_IMAGE_MAX_WIDTH: max width (in px) of the images.
MOMO_PARENT_INDEX: the loop index (Jinja loop.index, 1-based) of attrs to
                   insert the parent to.
MOMO_CACHE: a simple cache.
MOMO_USE_BOOTSTRAP_STYLES: whether to use Bootstrap styles (default to True).
MOMO_USE_BOOTSTRAP_SCRIPTS: whether to use Bootstrap scripts (default to True).
"""


class Flask(Plugin):
    def setup(self):
        bucket_name = self.settings.bucket.name
        self.configs = self.settings.plugins.get(
            'flask', {}).get(bucket_name, {})
        flask_dir = os.path.join(
            self.settings.settings_dir, 'flask', bucket_name)
        sys.path.append(flask_dir)

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
        app.config['MOMO_HEADER_NODE_COUNT'] = self.configs.get(
            'header_node_count', False)
        header_node_count_levels = self.configs.get('header_node_count_levels')
        app.config['MOMO_HEADER_NODE_COUNT_LEVELS'] = (
            to_list(header_node_count_levels)
            if header_node_count_levels else None)
        app.config['MOMO_INDEX_TABLE'] = self.configs.get('index_table', False)

        app.config['MOMO_PAGINATION_RECORD_NAME'] = self.configs.get(
            'pagination_record_name', 'node')
        app.config['MOMO_PAGINATION_INDEX_PER_PAGE'] = self.configs.get(
            'pagination_index_per_page', 30)
        app.config['MOMO_PAGINATION_NODE_PER_PAGE'] = self.configs.get(
            'pagination_node_per_page', 30)
        app.config['MOMO_PAGINATION_SEARCH_PER_PAGE'] = self.configs.get(
            'pagination_search_per_page', 30)
        app.config['MOMO_PAGINATION_DISPLAY_MSG'] = self.configs.get(
            'pagination_display_msg', '{total} {record_name}s.')

        app.config['MOMO_VIEW'] = self.configs.get('view', 'list')
        app.config['MOMO_VIEW_INDEX'] = self.configs.get('view_index')
        app.config['MOMO_VIEW_SEARCH'] = self.configs.get('view_search')
        app.config['MOMO_VIEW_NODE'] = self.configs.get('view_node')
        app.config['MOMO_LIST_NODE_ATTRS'] = \
            self.configs.get('list_node_attrs', True)
        app.config['MOMO_ROOT_REVERSED'] = self.configs.get('root_reversed')
        app.config['MOMO_MERGE_NODES'] = self.configs.get('merge_nodes')
        app.config['MOMO_CASE_INSENSITIVE'] = self.configs.get(
            'case_insensitive', False)
        app.config['MOMO_STRING_SEPARATOR'] = self.configs.get(
            'string_separator')
        app.config['MOMO_HOLDER_SIZE'] = self.configs.get(
            'holder_size', '125x125')
        app.config['MOMO_IMAGE_MAX_WIDTH'] = self.configs.get(
            'image_max_width')
        app.config['MOMO_PARENT_INDEX'] = self.configs.get('parent_index', 1)
        app.config['MOMO_CACHE'] = {}

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

        # if set, the path attr will render link with the given ip:port instead
        # of same as the flask app's ip:port
        app.config['MOMO_FILE_SERVING_ADDRESS'] = \
            self.configs.get('file_serving_address')

        # flask-bootstrap
        app.config['MOMO_USE_BOOTSTRAP_STYLES'] = \
            self.configs.get('use_bootstrap_styles', True)
        app.config['MOMO_USE_BOOTSTRAP_SCRIPTS'] = \
            self.configs.get('use_bootstrap_scripts', True)

    def _get_pinning_function(self, pinned_attrs):
        """Return a (template filter) function that reorders attrs based on
        the given pinned attrs."""

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
        if self.configs.get('debug') is not None:
            debug = self.configs.get('debug')
        else:
            debug = FLASK_DEFAULT_DEBUG
        print('Serving on http://{}:{} with debug = {}...'.format(
              host, port, debug),
              file=sys.stderr)

        def _debug_run():
            app.run(
                host=host,
                port=port,
                debug=debug,
                use_reloader=False,
            )

        def _run():
            # TODO: make log argument (access log) configurable
            http_server = WSGIServer((host, port), app, log=None)
            http_server.serve_forever()

        if debug:
            _debug_run()
        else:
            _run()


plugin = Flask()
