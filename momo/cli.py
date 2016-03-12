# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from momo import plugins
from momo.actions.default import NodeAction, AttributeAction
from momo.core import Element
from momo.settings import settings
from momo.utils import utf8_decode
import argparse


def parse_args():
    parser = argparse.ArgumentParser(prog='momo')
    parser.add_argument('-b', '--bucket',
                        help="name of the bucket to use")
    subparsers = parser.add_subparsers(dest='subparser_name')
    pls = subparsers.add_parser('ls')
    subparser_ls(pls)
    ppl = subparsers.add_parser('pl')
    subparser_pl(ppl)
    args = parser.parse_args()
    return args


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
                   help='run a command on an element')
    p.add_argument('-c', '--cmd', nargs='?', const=False, metavar='NUM',
                   help='execute saved command(s)')


def subparser_pl(p):
    """
    The parser for sub-command "pl".
    """
    p.add_argument('plugin', help='run a plugin')


def do_ls(args):
    names = args.names
    bucket = settings.bucket
    parent = None
    elem = bucket.root
    name_or_num = None
    while names:
        parent = elem
        name_or_num = names.pop(0)
        elem = elem.ls(name_or_num=name_or_num,
                       show_path=args.path)
    action = None
    # XXX: a list item in an attribute content
    if not isinstance(elem, Element):
        action = AttributeAction(parent, name_or_num)
    elif elem.is_attr:
        action = AttributeAction(elem)
    elif elem.is_node:
        action = NodeAction(elem)
    if args.open:
        action.open()
    elif args.run is not None:
        if args.run is False:
            action.run()
        else:
            action.run(cmd=args.run)
    elif args.cmd is not None:
        if args.cmd is False:
            if isinstance(elem, Element):
                action.cmds()
            else:
                action.cmd()
        else:
            action.cmd(num=args.cmd)
    else:
        if isinstance(elem, Element):
            elem.ls(show_path=args.path)


def do_pl(args):
    plugin = getattr(plugins, args.plugin).plugin
    plugin.setup()
    plugin.run()


def main():
    args = parse_args()
    if args.subparser_name == 'ls':
        do_ls(args)
    elif args.subparser_name == 'pl':
        do_pl(args)
