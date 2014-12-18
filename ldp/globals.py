# -*- coding: utf-8 -*-
"""
    ldp.globals
    ~~~~~~~~~~~~~

    Defines all the global objects that are proxies to the current
    active context.
"""
import sys
import types

from werkzeug.local import LocalStack, LocalProxy

class GlobalsModule(types.ModuleType):
    __all__ = ('_dataset_ctx_stack', 'dataset', 'data', 'aggregation', 'resource')
    __package__ = __package__
    __loader__ = __loader__
    __name__ = __name__
    __path__ = __file__
    if '__initializing__' in locals():
        __initializing__ = __initializing__
    _dataset_ctx_stack = LocalStack()
    _resource_ctx_stack = LocalStack()

    def __init__(self, *args, **kwargs):
        super(GlobalsModule, self).__init__(*args, **kwargs)
        self.dataset = LocalProxy(self._lookup_dataset)
        self.data = LocalProxy(self._lookup_data_mapping)
        self.aggregation = LocalProxy(self._lookup_data_aggregation)
        self.resource = LocalProxy(self._lookup_resource_stack)

    def _lookup_resource_stack(self):
        top = self._resource_ctx_stack.top
        if top is None:
            raise RuntimeError('working outside of resource context')
        return top

    def _lookup_dataset(self):
        top = self._dataset_ctx_stack.top
        if top is None:
            raise RuntimeError('working outside of dataset context')
        return top

    def _lookup_data_mapping(self):
        return self.dataset.g

    def _lookup_data_aggregation(self):
        return self.data.aggregation

    def _lookup_named_graph(self, name):
        return self.data[name]

    def __getattr__(self, name):
        from werkzeug.local import LocalProxy
        from functools import partial
        if name not in self.__dict__:
            self.__dict__[name] = LocalProxy(
                partial(self._lookup_named_graph, name))

        return self.__dict__[name]

sys.modules[__name__] = GlobalsModule(__name__, __doc__)
