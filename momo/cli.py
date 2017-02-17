# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import logging
import os
import sys
from cliff.app import App
from cliff.command import Command
from cliff.commandmanager import CommandManager
from momo import plugins
from momo.backends import OrderedDict
from momo.core import configs, AttrError
from momo.settings import settings
from momo.utils import txt_type, utf8_decode, page_lines, eval_path
import momo.core
import inspect


INDENT_UNIT = '  '


class MomoCliApp(App):
    def __init__(self):
        super(MomoCliApp, self).__init__(
            description='momo cli',
            version='0.1.0',
            command_manager=CommandManager('momo.cli'),
            )
        self.bucket = None
        self.cbn = None

    def configure_logging(self):
        """Create logging handlers for any log output.
        """
        root_logger = logging.getLogger()

        # Set up logging to a file
        if self.options.log_file:
            file_handler = logging.FileHandler(
                filename=self.options.log_file,
            )
            formatter = logging.Formatter(self.LOG_FILE_MESSAGE_FORMAT)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        # Always send higher-level messages to the console via stderr
        console = logging.StreamHandler(self.stderr)
        console_level = {0: logging.WARNING,
                         1: logging.INFO,
                         2: logging.DEBUG,
                         }.get(self.options.verbose_level, logging.WARNING)
        console.setLevel(console_level)
        formatter = logging.Formatter(self.CONSOLE_MESSAGE_FORMAT)
        console.setFormatter(formatter)
        root_logger.addHandler(console)
        return

    def build_option_parser(self, description, version,
                            argparse_kwargs=None):
        parser = super(MomoCliApp, self).build_option_parser(
            description, version, argparse_kwargs)
        parser.add_argument('-b', '--bucket', default='default',
                            help='bucket name')
        return parser

    def initialize_app(self, argv):
        self.use_bucket(self.options.bucket)

    def use_bucket(self, bucket_name):
        settings.cbn = bucket_name
        if self.cbn != bucket_name:  # only load bucket from path if changed
            self.cbn = bucket_name
            self.bucket = settings.bucket

    def run_subcommand(self, argv):
        try:
            subcommand = self.command_manager.find_command(argv)
        except ValueError as err:
            # If there was no exact match, try to find a fuzzy match
            the_cmd = argv[0]
            fuzzy_matches = self.get_fuzzy_matches(the_cmd)
            if fuzzy_matches:
                article = 'a'
                if self.NAME[0] in 'aeiou':
                    article = 'an'
                self.stdout.write('%s: \'%s\' is not %s %s command. '
                                  'See \'%s --help\'.\n'
                                  % (self.NAME, the_cmd, article,
                                      self.NAME, self.NAME))
                self.stdout.write('Did you mean one of these?\n')
                for match in fuzzy_matches:
                    self.stdout.write('  %s\n' % match)
            else:
                if self.options.debug:
                    raise
                else:
                    self.LOG.error(err)
            return 2
        cmd_factory, cmd_name, sub_argv = subcommand
        kwargs = {}
        if 'cmd_name' in inspect.getargspec(cmd_factory.__init__).args:
            kwargs['cmd_name'] = cmd_name
        cmd = cmd_factory(self, self.options, **kwargs)
        err = None
        result = 1
        try:
            self.prepare_to_run_command(cmd)
            full_name = (cmd_name
                         if self.interactive_mode
                         else ' '.join([self.NAME, cmd_name])
                         )
            cmd_parser = cmd.get_parser(full_name)
            parsed_args = cmd_parser.parse_args(sub_argv)
            result = cmd.run(parsed_args)
        except Exception as err:
            if self.options.debug:
                self.LOG.exception(err.message)
            else:
                self.LOG.error(err.message)
            try:
                self.clean_up(cmd, result, err)
            except Exception as err2:
                if self.options.debug:
                    self.LOG.exception(err2.message)
                else:
                    self.LOG.error('Could not clean up: %s', err2.message)
            if self.options.debug:
                raise
        else:
            try:
                self.clean_up(cmd, result, None)
            except Exception as err3:
                if self.options.debug:
                    self.LOG.exception(err3)
                else:
                    self.LOG.error('Could not clean up: %s', err3)
        return result


class External(Command):
    """
    Run external shell commands.
    """
    def get_parser(self, prog_name):
        """
        The parser for sub-command "e".
        """
        p = super(External, self).get_parser(prog_name)
        p.add_argument('cmd', help='external command')
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        os.system(parsed_args.cmd)


class Chdir(Command):
    """
    Change directory.
    """
    def get_parser(self, prog_name):
        """
        The parser for sub-command "e".
        """
        p = super(Chdir, self).get_parser(prog_name)
        p.add_argument('directory', help='target directory')
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        os.chdir(parsed_args.directory)


class Ls(Command):
    """List elements."""

    def get_parser(self, prog_name):
        """
        The parser for sub-command "ls".
        """
        p = super(Ls, self).get_parser(prog_name)
        p.add_argument('names', nargs='*', type=utf8_decode,
                       help='names or numbers to identify element')
        p.add_argument('-s', '--short', action='store_true',
                       help='show only names')
        p.add_argument('-p', '--path', action='store_true',
                       help='show full path')
        p.add_argument('-o', '--open', action='store_true',
                       help='open an element')
        p.add_argument('-r', '--run', nargs='?', const=False,
                       metavar='COMMAND',
                       help='run a command on an element', type=utf8_decode)
        p.add_argument('-c', '--cmd', nargs='?', const=False, metavar='NUM',
                       help='execute saved command(s)', type=utf8_decode)
        p.add_argument('-x', '--expand', action='store_true',
                       help='show expanded attributes')
        p.add_argument('-t', '--type',
                       help='element type')
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        do_ls(self.app.bucket, parsed_args, self.parser)


class Add(Command):
    """
    Add a node or attribute.
    """
    def get_parser(self, prog_name):
        """
        The parser for sub-command "add".
        """
        p = super(Add, self).get_parser(prog_name)
        p.add_argument('names', nargs='*', type=utf8_decode,
                       help='names or numbers to identify element')
        p.add_argument('-n', '--name', type=utf8_decode,
                       help='name of the element to add')
        p.add_argument('-c', '--content', action='append', required=True,
                       type=utf8_decode, help='contents')
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        do_add(self.app.bucket, parsed_args, self.parser)


class AddPath(Command):
    """
    Shortcut to add a path.
    """
    def get_parser(self, prog_name):
        """
        The parser for sub-command "add".
        """
        p = super(AddPath, self).get_parser(prog_name)
        p.add_argument('names', nargs='*', type=utf8_decode,
                       help='names or numbers to identify element')
        p.add_argument('-p', '--path', type=utf8_decode, required=True,
                       help='path to add')
        p.add_argument('-n', '--name', type=utf8_decode,
                       help='name of the node')
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        do_add_path(self.app.bucket, parsed_args, self.parser)


class Remove(Command):
    """
    Remove a node or attribute.
    """
    def get_parser(self, prog_name):
        """
        The parser for sub-command "add".
        """
        p = super(Remove, self).get_parser(prog_name)
        p.add_argument('names', nargs='*', type=utf8_decode,
                       help='names or numbers to identify element')
        p.add_argument('-y', '--yes', action='store_true',
                       help='yes to prompt')
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        do_remove(self.app.bucket, parsed_args, self.parser)


class Plugin(Command):
    """Use plugins."""

    def get_parser(self, prog_name):
        """
        The parser for sub-command "pl".
        """
        p = super(Plugin, self).get_parser(prog_name)
        p.add_argument('plugin', help='run a plugin')
        p.add_argument('args', nargs='?', help='positional arguments')
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        do_pl(parsed_args.plugin, parsed_args.args)


class Use(Command):
    """Use a bucket."""
    def get_parser(self, prog_name):
        """
        The parser for sub-command "use".
        """
        p = super(Use, self).get_parser(prog_name)
        p.add_argument('bucket', help='bucket name')

        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        self.app.use_bucket(parsed_args.bucket)


class Reload(Command):
    """Reload current bucket from path."""
    def get_parser(self, prog_name):
        """
        The parser for sub-command "reload".
        """
        p = super(Reload, self).get_parser(prog_name)
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        self.app.bucket = settings.bucket


class Buckets(Command):
    """Show available buckets."""
    def get_parser(self, prog_name):
        """
        The parser for sub-command "buckets".
        """
        p = super(Buckets, self).get_parser(prog_name)
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        for name, path in settings.buckets.items():
            print('%s: %s' % (name, path))


class Dump(Command):
    """Write the current bucket to disk."""
    def get_parser(self, prog_name):
        """
        The parser for sub-command "save".
        """
        p = super(Dump, self).get_parser(prog_name)
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        self.app.bucket.dump()
        print('bucket "%s" has been saved.' % self.app.cbn)


def do_ls(bucket, args, parser):
    root = bucket.root
    root.cache_lines = True
    with momo.core.lines() as lines:
        indexer = Indexer(
            elem=root,
            parser=parser,
            names=args.names,
            unordered=True,
            show_path=args.path,
            elem_type=args.type,
            expand_attr=args.expand,
            cache_lines=True,
            no_output=False,
            short_output=args.short,
            to_open=args.open,
            run=args.run,
            cmd=args.cmd,
        )
        indexer.ls()
        page_lines(lines)


def do_add(bucket, args, parser):
    root = bucket.root
    root.cache_lines = True
    indexer = Indexer(
        elem=root,
        parser=parser,
        names=args.names,
        unordered=True,
        cache_lines=False,
        no_output=True,
    )
    elem = indexer.get()
    name = args.name
    contents = _parse_contents(args.content, parser)
    if not elem.is_attr:
        if name is None:
            parser.error(
                'argument -n/--name is required for adding elements to nodes '
                'and non-list-type attributes')
        elem.add(name, contents)
    else:
        elem.add(contents)
    if isinstance(contents, list):
        msg = 'list-type attribute "%s" added' % name
    elif isinstance(contents, OrderedDict):
        msg = 'node "%s" added' % name
    else:
        msg = 'attribute "%s" added' % name
    print('%s to %s "%s"' % (msg, elem.type.lower(), elem))


def do_add_path(bucket, args, parser):
    root = bucket.root
    root.cache_lines = True
    indexer = Indexer(
        elem=root,
        parser=parser,
        names=args.names,
        unordered=True,
        cache_lines=False,
        no_output=True,
    )
    elem = indexer.get()
    path = eval_path(args.path)
    name = args.name or os.path.basename(path)
    content = OrderedDict([('path', path)])
    elem.add(name, content)
    print('file "%s" added to %s "%s"' % (name, elem.type.lower(), elem))


def do_remove(bucket, args, parser):
    root = bucket.root
    root.cache_lines = True
    indexer = Indexer(
        elem=root,
        parser=parser,
        names=args.names,
        unordered=True,
        cache_lines=False,
        no_output=True,
    )
    elem = indexer.get()
    parent = elem.parent
    parent.delete(elem.name)
    print('%s "%s" removed from %s "%s"' % (
          elem.type.lower(), elem, parent.type.lower(), parent))


def _parse_contents(content, parser):
    is_attr = False
    is_node = False
    res = None
    for c in content:
        if ':' in c:
            outs = c.split(':')
            if len(outs) != 2:
                parser.error('incorrect format for content "%s"' % c)
            if is_attr:
                parser.error(
                    'cannot mix node-type contents '
                    'with attribute-type contents')
            is_node = True
            if res is None:
                res = OrderedDict()
            outs = map(lambda x: x.strip(), outs)
            key, value = outs
            if key not in res:
                res[key] = value
            else:
                parser.error(
                    'duplicate name "%s" for node-type content' % key)
        else:
            if is_node:
                parser.error(
                    'cannot mix node-type contents '
                    'with attribute-type contents')
            is_attr = True
            if res is None:
                res = []
            res.append(c)

    if isinstance(res, list):
        if len(res) == 1:
            res = res[0]
    return res


def do_pl(plugin, args):
    """
    :param plugin: plugin's name.
    :param extra_args: extra positional arguments to the plugin program.
    """
    plugin = getattr(plugins, plugin).plugin
    plugin.setup()
    if args is not None:
        args = args.split()
    plugin.run(args=args)


class Indexer(object):
    def __init__(self, elem, parser, names, unordered=True, show_path=False,
                 elem_type=None, expand_attr=False, cache_lines=False,
                 no_output=False, short_output=False, to_open=False, run=False,
                 cmd=False):
        self.elem = elem
        configs.cache_lines = cache_lines
        configs.no_output = no_output
        configs.short_output = short_output
        self.parser = parser
        self.names = names
        self.unordered = unordered
        self.show_path = show_path
        self.elem_type = elem_type
        self.expand_attr = expand_attr
        self.to_open = to_open
        self.run = run
        self.cmd = cmd

    def ls(self):
        self._ls(return_elem=False)

    def get(self):
        return self._ls(return_elem=True)

    def _ls(self, return_elem):
        elem = self.elem
        elem.cache_lines = True
        name_or_num = None
        parent = None
        names = list(self.names)
        while names and parent is not elem:
            parent = elem
            name_or_num = names.pop(0)
            elem = self.ls_elem(elem, name_or_num=name_or_num,
                                unordered=self.unordered,
                                show_path=self.show_path,
                                expand_attr=self.expand_attr)
        if return_elem:
            return elem
        action = elem.action
        if elem.is_attr and elem.is_item:
            if names:
                self.parser.error('too many names or numbers')
        if self._ls_action(action):
            self.ls_elem(elem,
                         show_path=self.show_path,
                         elem_type=self.elem_type,
                         unordered=self.unordered,
                         expand_attr=self.expand_attr)

    def _ls_action(self, action):
        if self.to_open:
            action.open()
        elif self.run is not None:
            if self.run is False:
                action.run()
            else:
                action.run(cmd=self.run)
        elif self.cmd is not None:
            if self.cmd is False:
                if action.elem.is_attr and action.elem.is_item:
                    action.cmd()
                else:
                    action.cmds()
            else:
                action.cmd(num=self.cmd)
        else:
            return True

    def ls_elem(self, elem, *args, **kwargs):
        if elem.is_node:
            return Indexer.node_ls(elem, *args, **kwargs)
        elif elem.is_attr:
            return Indexer.attr_ls(elem, *args, **kwargs)

    @staticmethod
    def node_ls(node, name_or_num=None, show_path=False, sort_by=None,
                unordered=False, elem_type=None, **kwargs):
        """
        List and print elements of the Node object.  If `name_or_num` is not
        None, then return the element that matches.

        :param name_or_num: element name or number.  The name has higher
                            precedence than number.
        :param show_path: whether to show path to the element.
        :param sort_by: the name of the sorting key.  If it is None, then the
                        sorting key is the element name.  If it is a name, then
                        the content of the attribute with this name is used as
                        the key.
        :param unordered: whether to present elements unordered.  If it is
                          True, the original order in the document is used.
        :param elem_type: the element type.  If None, then all types are
                          included. Otherwise, it is one of "file",
                          "directory", "node", and "attribute".

        :return: the element that matches `name_or_num` (if it is not None)
        """
        if show_path and not node.is_root:
            node._print_path()
        if name_or_num is None:
            Indexer._node_ls_all(node, show_path, sort_by, unordered,
                                 elem_type)
        else:
            elem = None
            try:
                name_or_num = int(name_or_num)
            except ValueError:
                pass
            if isinstance(name_or_num, int):
                if str(name_or_num) in node.elems:
                    elem = node.get_elem_by_name(name_or_num)
                else:
                    elem = node.get_elem_by_num(
                        name_or_num, sort_by, unordered, elem_type)
            else:
                elem = node.get_elem_by_name(name_or_num)
            return elem

    @staticmethod
    def _node_ls_all(node, show_path, sort_by, unordered, elem_type):
        try:
            indent = ''
            if show_path:
                indent = INDENT_UNIT * node.level
            vals = node.get_vals(sort_by, unordered, elem_type)
            width = len(str(len(vals)))
            fmt = '%s%{}d [%s] %s'.format(width)
            for num, elem in enumerate(vals, start=1):
                if not configs.short_output:
                    node.lines.append(
                        fmt % (indent, num, elem.type[0], elem.name))
                else:
                    node.lines.append(elem.name)
        finally:
            node.flush_lines()

    @staticmethod
    def attr_lsattr(attr, name_or_num, show_path=False, expand_attr=False):
        """List attribute content."""
        try:
            if not attr.has_items:
                raise AttrError('cannot list non-list-type attribute')
            indent = ''
            if show_path:
                indent = INDENT_UNIT * (attr.level + 1)
            try:
                name_or_num = int(name_or_num)
            except ValueError:
                msg = 'must use a integer to index list-type attribute'
                raise AttrError(msg)
            content = attr.content
            if expand_attr:
                content = attr.parent.action.expand_attr(attr.name)
            val = content[name_or_num - 1]
            if not configs.short_output:
                attr.lines.append(
                    '%s%s[%d]: %s' % (indent, attr.name, name_or_num, val))
            else:
                attr.lines.append(val)
            attr._index = name_or_num
            return attr
        finally:
            attr.flush_lines()

    @staticmethod
    def attr_ls(attr, name_or_num=None, show_path=False, expand_attr=False,
                **kwargs):
        """
        List content of the attribute. If `name_or_num` is not None, return
        the matched item of the content.
        """
        if name_or_num is None:
            Indexer._attr_ls_all(attr, show_path, expand_attr)
        else:
            return Indexer.attr_lsattr(name_or_num, show_path, expand_attr)

    @staticmethod
    def _attr_ls_all(attr, show_path, expand_attr):
        try:
            if attr._index is not None:
                return
            indent = ''
            if show_path:
                indent = INDENT_UNIT * attr.level
            content = attr.content
            if expand_attr:
                content = attr.parent.action.expand_attr(attr.name)
            if attr.has_items:
                if not configs.short_output:
                    attr.lines.append('%s%s:' % (indent, attr.name))
                indent += INDENT_UNIT
                width = len(str(len(content)))
                fmt = '%s%{}d %s'.format(width)
                for num, item in enumerate(content, start=1):
                    if not configs.short_output:
                        attr.lines.append(fmt % (indent, num, item))
                    else:
                        attr.lines.append(item)
            elif isinstance(content, (txt_type, bool, int, float)):
                if not configs.short_output:
                    attr.lines.append(
                        '%s%s: %s' % (indent, attr.name, content))
                else:
                    attr.lines.append(content)
            elif content is None:
                if not configs.short_output:
                    attr.lines.append('%s%s: %s' % (indent, attr.name, ''))
            else:
                raise AttrError('unknown type for attribute content')
        finally:
            attr.flush_lines()


def main(argv=sys.argv[1:]):
    momocli = MomoCliApp()
    return momocli.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
