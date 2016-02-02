from __future__ import absolute_import
import yaml


class Bucket(object):
    """
    The Bucket class.

    :param name: name of the bucket.
    :param path: path to the bucket file.

    """

    def __init__(self, name, path):
        self.name = name
        self.path = path

    def load(self):
        """
        Load the bucket.

        :return: the loaded document.

        """
        with open(self.path) as f:
            return yaml.load(f.read())

    def dump(self, document):
        """
        Dump the document to the bucket file.
        """
        with open(self.path, 'w') as f:
            yaml.dump(document, f, default_flow_style=False)
