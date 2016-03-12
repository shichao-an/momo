# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import errno
import os
import sh
import six
import shlex
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


def utf8_decode(s):
    res = s
    if isinstance(res, six.binary_type):
        res = s.decode('utf-8')
    return res


def utf8_encode(s):
    res = s
    if isinstance(res, six.text_type):
        res = s.encode('utf-8')
    return res


def run_cmd(cmd_str=None, cmd=None, cmd_args=None, stdout=sys.stdout,
            stderr=sys.stderr, stdin=None):
    """
    :param cmd_str: the command string.
    :param cmd: the command.  If `cmd` is not None, it takes precedence over
                `cmd_str`.
    :param cmd_args: the list of command arguments.  If `cmd_args` is not
                     None, it takes precedence over `cmd_str`.
    """
    sh_kwargs = {
            '_out': stdout,
            '_err': stderr,
            '_in': stdin
    }
    comps = []
    if cmd_str is not None:
        comps = shlex.split(cmd_str)
    cmd = cmd or comps[0]
    run = sh.Command(cmd)
    if cmd_args is None and not comps[1:]:
        return run(**sh_kwargs)
    args = cmd_args or comps[1:]
    return run(*args, **sh_kwargs)


def mkdir_p(path):
    """mkdir -p path"""
    if PY3:
        return os.makedirs(path, exist_ok=True)
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
