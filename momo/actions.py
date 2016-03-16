from momo.utils import run_cmd, open_default, txt_type
import re


class Action(object):
    def __init__(self, elem):
        self.name = elem.name
        self.elem = elem


class ActionError(Exception):
    pass


class NodeAction(Action):
    """
    The NodeAction class.
    """
    def __init__(self, node):
        super(NodeAction, self).__init__(node)
        self.default_attrname = 'path'

    def expand_attr(self, attrname):
        """Expand attribute content"""
        attr = self.get_attr(attrname)
        if isinstance(attr.content, list):
            res = []
            subs = self._get_expand_subs(attrname)
            for item in attr.content:
                if self.is_expandable(item):
                    item = self.expand_str(item, subs, attrname)
                    res.append(item)
                else:
                    res.append(item)
            return res
        else:
            res = attr.content
            if self.is_expandable(res):
                res = self.expand_str(res, subs, attrname)
            return res

    def expand_str(self, s, exclude=None):
        """
        Expand a string.

        :param exclude: the attribute name to exclude from expansion.
        """
        subs = self._get_expand_subs()
        t = s.replace('{}', '{%s}' % self.default_attrname)
        if exclude is not None:
            del subs[exclude]
        return t.format(**subs)

    @staticmethod
    def is_expandable(s):
        if isinstance(s, txt_type):
            if re.search('{\S*}', s):
                return True
        return False

    def _get_expand_subs(self):
        subs = {
            k: self.elem.attrs[k].content for k in self.elem.attrs
        }
        return subs

    def get_attr(self, attrname):
        """
        Get an Attribute object by the name `attrname`.
        """
        return self.elem.attrs[attrname]

    def open(self, attrname='path'):
        attr = self.get_attr(attrname)
        open_default(attr.content)

    def run(self, cmd=None, expand=True):
        """
        Run a command on the attribute name.

        :param cmd: a command, command string or template.  If no "{}" or
                    "{attr}" is in `cmd`, the content of the "path" attribute
                    is appended to the end of it; otherwise, all occurrences
                    of "{}" and "{attr}" are replaced with corresponding
                    attribute contents. "{}" is expanded into the content of
                    the path attribute.
        """
        attr = self.get_attr(self.default_attrname)
        if cmd is None:
            run_cmd(cmd=attr.content)
        else:
            if self.is_expandable(cmd):
                cmd_str = self.expand_str(cmd)
            else:
                cmd_str = '%s %s' % (cmd, attr.content)
            run_cmd(cmd_str)

    def cmd(self, num=None, expand=True):
        """
        Execute a saved command, which is stored in the "cmds" attribute.
        """
        if num is None:
            num = 1
        cmd = self.get_attr('cmds').content[int(num) - 1]
        self.run(cmd)

    def cmds(self, expand=True):
        for cmd in self.get_attr('cmds').content:
            self.run(cmd)


class AttributeAction(Action):
    """
    The AttributeAction class.
    """
    def __init__(self, attr, item_num=None):
        super(AttributeAction, self).__init__(attr)
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
        if self.elem.has_items:
            node = self.elem.parent
            node.action.cmd(self.item_num)
        elif isinstance(self.elem.content, txt_type):
            self.run()
        else:
            raise ActionError('unknown attribute content type as commands')

    def cmds(self):
        """
        Run all commands in this attribute.
        """
        if self.elem.has_items:
            node = self.elem.parent
            node.action.cmds()
        elif isinstance(self.elem.content, txt_type):
            self.run()
        else:
            raise ActionError('unknown attribute content type as commands')
