import re
from inspect import getmembers, isfunction


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
