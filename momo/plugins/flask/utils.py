import re
from inspect import getmembers, isfunction
from momo.utils import txt_type, bin_type


FALSE_STR_PATTREN = '^(0|false|False)$'


def get_public_functions(module):
    """Get public functions in a module. Return a dictionary of function names
    to objects."""
    return {
        o[0]: o[1] for o in getmembers(module, isfunction)
        if not o[0].startswith('_')
    }


def str_to_bool(s):
    if re.match(FALSE_STR_PATTREN, s):
        return False
    return True


def to_list(value, sep=','):
    if isinstance(value, list):
        return value
    elif isinstance(value, (txt_type, bin_type)):
        return value.split(',')
    else:
        return [value]


def split_by(s, sep=','):
    return [item.strip() for item in filter(lambda x: x.strip(), s.split(sep))]
