from __future__ import absolute_import
from momo.backends.base import Document
import ruamel.yaml


class BucketDocument(Document):
    """
    The BucketDocument class for the YAML backend.

    :param name: name of the bucket.
    :param path: path to the bucket document.

    """

    def __init__(self, name, path):
        super(BucketDocument, self).__init__(name, path)

    def load(self):
        """
        Load the bucket.

        :return: the loaded content.

        """
        with open(self.path) as f:
            return ruamel.yaml.load(f.read(), ruamel.yaml.RoundTripLoader)

    def dump(self, content):
        """
        Dump the content to the bucket file.
        """
        with open(self.path, 'w') as f:
            ruamel.yaml.round_trip_dump(
                content, f, indent=4, block_seq_indent=2, width=500)
