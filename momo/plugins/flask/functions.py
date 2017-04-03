# template global functions
# make sure not to conflict with built-ins:
# http://jinja.pocoo.org/docs/2.9/templates/#list-of-global-functions

from flask.helpers import url_for as _url_for
from flask_paginate import Pagination


def paginate(page, total, per_page, config):
    record_name = config['MOMO_PAGINATION_RECORD_NAME']
    display_msg = config['MOMO_PAGINATION_DISPLAY_MSG']
    pagination = _paginate(
        page=page,
        total=total,
        per_page=per_page,
        record_name=record_name,
        display_msg=display_msg,
    )
    return pagination


def _paginate(page, total, per_page, record_name, display_msg):
    pagination = Pagination(
        page=page,
        total=total,
        per_page=per_page,
        bs_version=3,
        show_single_page=False,
        record_name=record_name,
        display_msg=display_msg,
    )
    return pagination


def get_page(request):
    return request.args.get('page', default=1, type=int)


def toggle_arg(endpoint, request, arg, value, **kwargs):
    """Toggle request arguments.

    :param endpoint: endpoint name.
    :param request: request object.
    :param arg: request argument name to toggle.
    :param value: intial value for the toggled argument.
    :param kwargs: keyword arguments to preserve.
    """
    args = request.args.to_dict()
    if arg in args:
        args.pop(arg)
    else:
        args[arg] = value
    args.update(request.view_args)
    args.update(kwargs)
    return _url_for(endpoint, **args)
