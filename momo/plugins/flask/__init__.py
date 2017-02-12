import os
import jinja2
from momo.plugins.base import Plugin
from momo.plugins.flask.app import app

FLASK_DEFAULT_HOST = '127.0.0.1'
FLASK_DEFAULT_PORT = '7000'
FLASK_DEFAULT_DEBUG = True


class Flask(Plugin):
    def setup(self):
        bucket_name = self.settings.bucket.name
        self.configs = self.settings.plugins.get(
            'flask', {}).get(bucket_name, {})
        flask_root_dir = os.path.join(
            self.settings.settings_dir, 'flask')
        self.flask_dir = os.path.join(flask_root_dir, bucket_name)
        self.template_dir = os.path.join(self.flask_dir, 'templates')
        self.static_dir = os.path.join(self.flask_dir, 'static')
        self._reset_loader()

    def _reset_loader(self):
        """Add user-defined template folder."""
        app.jinja_loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(self.template_dir),
            app.jinja_loader,
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
