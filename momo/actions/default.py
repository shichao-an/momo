from momo.actions.base import Action
import os
import platform
import sh


def open_default(path):
    if platform.system() == 'Darwin':
        sh.open(path)
    elif os.name == 'nt':
        os.startfile(path)
    elif os.name == 'posix':
        run = sh.Command('xdg-open')
        run()


class NodeAction(Action):
    def __init__(self, node):
        super(NodeAction, self).__init__(node.name, node)

    def get_attr(self, attrname):
        """
        Get an Attribute object by the name `attrname`.
        """
        return self.elem.attrs[attrname]

    def open(self, attrname='path'):
        attr = self.get_attr(attrname)
        open_default(attr.content)

    def run(self, cmd=None, attrname='path'):
        """
        Run a command on the attribute name.
        """
        attr = self.get_attr(attrname)
        if cmd is None:
            run = sh.Command(attr.content)
            run()
        else:
            run = sh.Command(cmd)
            run(attr.content)


class FileAction(NodeAction):
    def __init__(self, name, file):
        super(FileAction, self).__init__(file.name, file)


class AttributeAction(Action):
    def __init__(self, attr):
        super(AttributeAction, self).__init__(attr.name, attr)

    def open(self):
        open_default(self.elem.content)

    def run(self, cmd=None):
        if cmd is None:
            run = sh.Command(self.elem.content)
            run()
        else:
            run = sh.Command(cmd)
            run(self.elem.content)
