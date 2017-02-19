# template global functions
# make sure not to conflict with built-ins:
# http://jinja.pocoo.org/docs/2.9/templates/#list-of-global-functions

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
