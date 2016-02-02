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
