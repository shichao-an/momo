from momo.plugins.base import Plugin
from momo.plugins.flask.app import app


class Flask(Plugin):
    def setup(self):
        bucket_name = self.settings.bucket.name
        self.configs = self.settings.plugins.get(
            'flask', {}).get(bucket_name, {})

    def run(self, args=None):
        app.run(
            host=self.configs['host'],
            port=self.configs['port'],
        )

plugin = Flask()
