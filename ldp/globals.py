# -*- coding: utf-8 -*-
"""
    ldp.globals
    ~~~~~~~~~~~~~

    Defines all the global objects that are proxies to the current
    active context.
"""

from functools import partial
from werkzeug.local import LocalStack, LocalProxy


def _lookup_dataset_object(name):
    top = _dataset_ctx_stack.top
    if top is None:
        raise RuntimeError('working outside of dataset context')
    return top


def _lookup_data_object():
    return ds._aggregated_graphs['data']

def _lookup_scheme_object():
    return ds._aggregated_graphs['scheme']

# context locals
_dataset_ctx_stack = LocalStack()
ds = LocalProxy(partial(_lookup_dataset_object, 'dataset'))
data = LocalProxy(_lookup_data_object)
scheme = LocalProxy(_lookup_scheme_object)