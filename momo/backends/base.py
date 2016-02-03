class Document(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def load(self):
        raise NotImplementedError

    def dump(self, content):
        raise NotImplementedError
