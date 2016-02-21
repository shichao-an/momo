from momo.actions.base import Action
import os
import platform
import re
import sh
import shlex
import sys


def run_cmd(cmd_str=None, cmd=None, cmd_args=None, stdout=sys.stdout,
            stderr=sys.stderr, stdin=None):
    """
    :param cmd_str: the command string.
    :param cmd: the command.  If `cmd` is not None, it takes precedence over
                `cmd_str`.
    :param cmd_args: the list of command arguments.  If `cmd_args` is not
                     None, it takes precedence over `cmd_str`.
    """
    sh_kwargs = {
            '_out': stdout,
            '_err': stderr,
            '_in': stdin
    }
    comps = []
    if cmd_str is not None:
        comps = shlex.split(cmd_str)
    cmd = cmd or comps[0]
    run = sh.Command(cmd)
    if cmd_args is None and not comps[1:]:
        return run(**sh_kwargs)
    args = cmd_args or comps[1:]
    return run(*args, **sh_kwargs)


class CommandParser(object):
    """
    The CommandParser class.

    :param cmd_str: a command or command string
    :param default: the attribute name to replace '{}'
    :param subs: a dictionary of substituions
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
            run_cmd(cmd=self.elem.content)
        else:
            run_cmd(cmd=cmd, cmd_args=[self.elem.content])
