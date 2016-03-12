from momo.utils import run_cmd, open_default
from momo.actions.base import Action
import re


class CommandParser(object):
    """
    The CommandParser class.

    :param cmd_str: a command or command string.
    :param default: the field name to replace '{}'.
    :param subs: a dictionary of substituions.
    """

    def __init__(self, cmd_str, default, subs):
        self.cmd_str = cmd_str
        self.default = default
        self.subs = subs

    def parse_cmd(self):
        if re.search('{\S*}', self.cmd_str):
            t = self.cmd_str.replace('{}', '{%s}' % self.default)
            return t.format(**self.subs)
        else:
            return '%s %s' % (self.cmd_str, self.subs[self.default])


class ActionError(Exception):
    pass


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

        :param cmd: a command, command string or template.  If no `{}` or
                    `{attr}` is in `cmd`, the content of attribute `attrname`
                    is appended to the end of it; otherwise, all occurrences
                    of `{}` and `{attr}` are replaced with corresponding
                    attribute contents.
        """
        attr = self.get_attr(attrname)
        if cmd is None:
            run_cmd(cmd=attr.content)
        else:
            subs = {k: self.elem.attrs[k].content for k in self.elem.attrs}
            parser = CommandParser(
                cmd_str=cmd,
                default=attrname,
                subs=subs
            )
            cmd_str = parser.parse_cmd()
            run_cmd(cmd_str)

    def cmd(self, num=None, attrname='path'):
        """
        Execute a saved command, which is stored in the `cmds` attribute.
        """
        if num is None:
            num = 1
        cmd = self.get_attr('cmds').content[int(num) - 1]
        self.run(cmd, attrname)

    def cmds(self, attrname='path'):
        for cmd in self.get_attr('cmds').content:
            self.run(cmd, attrname)


class FileAction(NodeAction):
    def __init__(self, name, file):
        super(FileAction, self).__init__(file.name, file)


class AttributeAction(Action):
    def __init__(self, attr, item_num=None):
        super(AttributeAction, self).__init__(attr.name, attr)
        num = item_num or 1
        self.item_num = int(num)

    def open(self):
        open_default(self.elem.content)

    def run(self, cmd=None):
        if cmd is None:
            run_cmd(cmd=self.elem.content)
        else:
            run_cmd(cmd=cmd, cmd_args=[self.elem.content])

    def cmd(self):
        """
        Run the command specified by `item_num`
        """
        if isinstance(self.elem.content, list):
            node = self.elem.parent
            node_action = NodeAction(node)
            node_action.cmd(self.item_num)
        elif isinstance(self.elem.content, str):
            self.run()
        else:
            raise ActionError('unknown attribute content type as commands')

    def cmds(self):
        """
        Run all commands in this attribute.
        """
        if isinstance(self.elem.content, list):
            node = self.elem.parent
            node_action = NodeAction(node)
            node_action.cmds()
        elif isinstance(self.elem.content, str):
            self.run()
        else:
            raise ActionError('unknown attribute content type as commands')
