from __future__ import print_function
import argparse
import os
import sh
import sys
import yaml


DEFAULT_MOMO_YML = os.environ.get('MOMO_YML') or '~/.momo.yml'
DIRS = {}
ITEMS = None

# file attr: func
DEFAULT_ACTIONS = {
    'image': sh.open,
    'path': sh.open,
}


def eval_path(path):
    return os.path.abspath(os.path.expanduser(path))


def load_yaml(filename=DEFAULT_MOMO_YML):
    with open(eval_path(filename)) as f:
        return yaml.load(f.read())


def parse_yaml(yml):
    """
    Parse a load YAML file per momo format: looking for 'name' and 'contents'
    """
    name = None
    contents = None
    for d in yml:
        if 'name' in d:
            name = d['name']
        if 'contents' in d:
            contents = d['contents']
    return name, contents


class Base(object):
    pass


class Directory(Base):
    def __init__(self, name, files=None):
        self.name = name
        self._files = files
        self.files = None
        self.filed = None

    def load(self):
        """Load files into self.files and self.filed"""
        if self.files is None:
            self.files = []
            for _f in self._files:
                filename = _f.keys()[0]
                f = File(filename)
                for attr in _f[filename]:
                    attr_name = attr.keys()[0]
                    if attr_name == 'path':
                        f.path = attr['path']
                    if attr_name == 'image':
                        f.image = attr['image']
                self.files.append(f)
        self.filed = {}
        for f in self.files:
            self.filed[f.name] = f

    def ls(self):
        if self.files is None:
            self.load()
        for i, f in enumerate(self.files, start=1):
            print('  ', i, f.name, sep='  ')

    def get_by_number(self, filen):
        if self.files is None:
            self.load()
        return self.files[filen - 1]

    def get_by_name(self, filen):
        if self.files is None:
            self.load()
        return self.filed[filen]


class File(Base):
    def __init__(self, name, path=None, image=None):
        self.name = name
        self.path = path
        self.image = image


def items_dirs():
    """
    Convert DIRS to list of items as ITEMS
    """
    global ITEMS
    ITEMS = DIRS.items()


def print_dirs():
    for i, item in enumerate(ITEMS, start=1):
        print(i, item[0], sep='  ')


def parse_args():
    parser = argparse.ArgumentParser(prog='momo')
    parser.add_argument('dirn', nargs='?', help='directory name or number')
    parser.add_argument('filen', nargs='?', help='file name or number')
    parser.add_argument('attrn', nargs='?', help='attr of the file')
    parser.add_argument('action', nargs='?', help='action on the attr')
    args = parser.parse_args()
    return args


def main():
    yml = load_yaml()
    name, contents = parse_yaml(yml)
    for d in contents:
        dirname = d.keys()[0]
        files = d[dirname]
        DIRS[dirname] = Directory(dirname, files)
    items_dirs()
    args = parse_args()
    dirn = args.dirn

    # Operate directories
    if dirn is None:
        print_dirs()
        sys.exit(0)
    try:
        dirn = int(dirn)
    except ValueError:
        pass
    if isinstance(dirn, int):
        directory = ITEMS[dirn - 1][1]
    else:
        directory = DIRS[dirn]

    # Operate files
    filen = args.filen
    if filen is None:
        directory.ls()
        sys.exit(0)
    try:
        filen = int(filen)
    except ValueError:
        pass
    if isinstance(filen, int):
        f = directory.get_by_number(filen)
    else:
        f = directory.get_by_name(filen)

    # Operate attrs on a file
    attrn = args.attrn
    if attrn is None:
        attrn = 'path'
    attr = getattr(f, attrn)

    # Operate actions
    action = args.action
    if action is None:
        func = DEFAULT_ACTIONS[attrn]
        func(attr)
    else:
        run = sh.Command(action)
        run(attr)
