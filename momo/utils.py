# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import os
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    bin_type = bytes
    txt_type = str
else:
    bin_type = str
    txt_type = unicode


def eval_path(path):
    return os.path.abspath(os.path.expanduser(path))


def smart_print(*args, **kwargs):
    args = filter(lambda x: x != '', args)
    print(*args, **kwargs)
