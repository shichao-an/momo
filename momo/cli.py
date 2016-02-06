from __future__ import print_function, absolute_import
from momo.settings import settings
import argparse


def parse_args():
    parser = argparse.ArgumentParser(prog='momo')
    parser.add_argument('-b', '--bucket',
                        help="name of the bucket to use")
    subparsers = parser.add_subparsers(dest='subparser_name',
                                       metavar='{ls}')
    pls = subparsers.add_parser('ls')
    subparser_ls(pls)
    args = parser.parse_args()
    return args


def subparser_ls(p):
    """
    The parser for sub-command "ls".
    """
    p.add_argument('names', nargs='*',
                   help='names or numbers to identify element')

    p.add_argument('-p', '--path', action='store_true',
                   help='show full path')


def do_ls(args):
    names = args.names
    bucket = settings.bucket
    node = bucket.root
    while names:
        name_or_num = names.pop(0)
        node = node.ls(name_or_num=name_or_num, show_path=args.path)
    node.ls(show_path=args.path)


def do_np(args):
    pass


def main():
    args = parse_args()
    print(args)
    if args.subparser_name == 'ls':
        do_ls(args)
    else:
        do_np(args)
