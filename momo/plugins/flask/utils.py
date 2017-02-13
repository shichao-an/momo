from inspect import getmembers, isfunction


def get_public_functions(module):
    """Get public functions in a module. Return a dictionary of function names
    to objects."""
    return {
        o[0]: o[1] for o in getmembers(module, isfunction)
        if not o[0].startswith('_')
    }
