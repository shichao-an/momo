from momo.settings import settings
import argparse
import sys


def fix_argv():
    """Fix sys.argv due to http://bugs.python.org/issue9253"""
    argv = set(sys.argv[1:])
    if 'down' not in argv and 'up' not in argv:
        sys.argv.append('__nop')


def parse_args():
    parser = argparse.ArgumentParser(prog='momo')
    args = parser.parse_args()
    parser.add_argument('-b', '--bucket',
                        help="name of the bucket to use")
    # subparsers
    subparsers = parser.add_subparsers(dest='subparser_name',
                                       metavar='{ls}')
    pnp = subparsers.add_parser('__nop')
    pls = subparsers.add_parser('ls')
    subparser_np(pnp)
    subparser_ls(pls)
    return args


def subparser_np(p):
    """
    The parser for no-op.
    """
    pass


def subparser_ls(p):
    """
    The parser for sub-command "ls".
    """
    p.add_argument('elems', nargs='*', help='element')


def do_ls(args):
    bucket = settings.bucket
    root = bucket.root
    elems = root.elems


def do_np(args):
    pass


def main():
    args = parse_args()
    if args.subparser_name == 'ls':
        do_ls(args)
    else:
        do_np(args)
