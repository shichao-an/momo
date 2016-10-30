from __future__ import absolute_import
from momo.backends.base import Document
import ruamel.yaml

INDENT = 4
BLOCK_SEQ_INDENT = 4
WIDTH = 500


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
            return ruamel.yaml.load(f.read(), ruamel.yaml.RoundTripLoader,
                                    preserve_quotes=True)

    def dump(self, content):
        """
        Dump the content to the bucket file.
        """
        with open(self.path, 'w') as f:
            ruamel.yaml.round_trip_dump(content, f,
                                        default_flow_style=False,
                                        indent=INDENT,
                                        block_seq_indent=BLOCK_SEQ_INDENT,
                                        width=WIDTH, tags=None)
