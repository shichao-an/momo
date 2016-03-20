# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from momo import plugins
from momo.settings import settings
from momo.utils import utf8_decode
import argparse


EXTRA_ARGS_PLUGINS = ('mkdocs')


def setup_parser():
    parser = argparse.ArgumentParser(prog='momo')
    parser.add_argument('-b', '--bucket',
                        help="name of the bucket to use")
    subparsers = parser.add_subparsers(dest='subparser_name')
    pls = subparsers.add_parser('ls')
    subparser_ls(pls)
    ppl = subparsers.add_parser('pl')
    subparser_pl(ppl)
    return parser


def subparser_ls(p):
    """
    The parser for sub-command "ls".
    """
    p.add_argument('names', nargs='*', type=utf8_decode,
                   help='names or numbers to identify element')
    p.add_argument('-p', '--path', action='store_true',
                   help='show full path')
    p.add_argument('-o', '--open', action='store_true',
                   help='open an element')
    p.add_argument('-r', '--run', nargs='?', const=False, metavar='COMMAND',
                   help='run a command on an element', type=utf8_decode)
    p.add_argument('-c', '--cmd', nargs='?', const=False, metavar='NUM',
                   help='execute saved command(s)', type=utf8_decode)
    p.add_argument('-x', '--expand', action='store_true',
                   help='show expanded attributes')
    p.add_argument('-t', '--type',
                   help='element type')


def subparser_pl(p):
    """
    The parser for sub-command "pl".
    """
    p.add_argument('plugin', help='run a plugin')


def do_ls(args, parser):
    names = args.names
    bucket = settings.bucket
    elem = bucket.root
    name_or_num = None
    parent = None
    while names and parent is not elem:
        parent = elem
        name_or_num = names.pop(0)
        elem = elem.ls(name_or_num=name_or_num,
                       show_path=args.path, expand_attr=args.expand)
    action = elem.action
    if elem.is_attr and elem.is_item:
        if names:
            parser.error('too many names or numbers')
    if ls_action(args, action):
        elem.ls(show_path=args.path, elem_type=args.type,
                expand_attr=args.expand)


def ls_action(args, action):
    if args.open:
        action.open()
    elif args.run is not None:
        if args.run is False:
            action.run()
        else:
            action.run(cmd=args.run)
    elif args.cmd is not None:
        if args.cmd is False:
            if action.elem.is_attr and action.elem.is_item:
                action.cmd()
            else:
                action.cmds()
        else:
            action.cmd(num=args.cmd)
    else:
        return True


def do_pl(args, extra_args):
    plugin = getattr(plugins, args.plugin).plugin
    plugin.setup()
    plugin.run(extra_args=extra_args)


def main():
    parser = setup_parser()
    args, extra_args = parser.parse_known_args()
    settings._cbn = args.bucket
    if args.subparser_name == 'ls':
        args = parser.parse_args()
        do_ls(args, parser)
    elif args.subparser_name == 'pl':
        do_pl(args, extra_args)
