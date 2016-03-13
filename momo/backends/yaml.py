from __future__ import absolute_import
from momo.backends.base import Document
import yaml
from collections import OrderedDict


# http://stackoverflow.com/a/21912744/1751342
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwargs):
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())
    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwargs)


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
            return ordered_load(f.read())

    def dump(self, content):
        """
        Dump the content to the bucket file.
        """
        with open(self.path, 'w') as f:
            ordered_dump(content, f, default_flow_style=False,
                         allow_unicode=True)
