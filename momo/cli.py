# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import logging
import sys
from cliff.app import App
from cliff.command import Command
from cliff.commandmanager import CommandManager
from momo import plugins
from momo.settings import settings
from momo.utils import utf8_decode, page_lines
import momo.core


class MomoCliApp(App):
    def __init__(self):
        super(MomoCliApp, self).__init__(
            description='momo cli',
            version='0.1.0',
            command_manager=CommandManager('momo.cli'),
            deferred_help=True,
            )
        self.bucket = None

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
        settings.cbn = self.options.bucket  # set bucket name
        self.bucket = settings.bucket


class Ls(Command):
    """List elements."""

    def get_parser(self, prog_name):
        """
        The parser for sub-command "ls".
        """
        p = super(Ls, self).get_parser(prog_name)
        p.add_argument('names', nargs='*', type=utf8_decode,
                       help='names or numbers to identify element')
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
        # save the parser
        self.parser = p
        return p

    def take_action(self, parsed_args):
        do_add(self.app.bucket, parsed_args, self.parser)


class Pl(Command):
    """Use plugins."""

    def get_parser(self, prog_name):
        """
        The parser for sub-command "pl".
        """
        p = super(Pl, self).get_parser(prog_name)
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
        settings.cbn = parsed_args.bucket
        self.app.bucket = settings.bucket


def do_ls(bucket, args, parser):
    elem = bucket.root
    elem.cache_lines = True
    with momo.core.lines() as lines:
        indexer = Indexer(
            elem=elem,
            parser=parser,
            names=args.names,
            unordered=True,
            show_path=args.path,
            elem_type=args.type,
            expand_attr=args.expand,
            cache_lines=True,
            no_output=False,
            to_open=args.open,
            run=args.run,
            cmd=args.cmd,
        )
        indexer.ls()
        page_lines(lines)


def do_add(bucket, args, parser):
    elem = bucket.root
    elem.cache_lines = True
    indexer = Indexer(
        elem=elem,
        parser=parser,
        names=args.names,
        unordered=True,
        cache_lines=False,
        no_output=True,
    )
    e = indexer.get()
    print(e)


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
                 no_output=False, to_open=False, run=False, cmd=False):
        self.elem = elem
        self.elem.cache_lines = cache_lines
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
            elem = elem.ls(name_or_num=name_or_num, unordered=self.unordered,
                           show_path=self.show_path,
                           expand_attr=self.expand_attr)
        if return_elem:
            return elem
        action = elem.action
        if elem.is_attr and elem.is_item:
            if names:
                self.parser.error('too many names or numbers')
        if self._ls_action(action):
            elem.ls(show_path=self.show_path, elem_type=self.elem_type,
                    unordered=self.unordered, expand_attr=self.expand_attr)

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


def main(argv=sys.argv[1:]):
    momocli = MomoCliApp()
    return momocli.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
