
import logging

from flask import Flask
from flask.helpers import _endpoint_from_view_func
from flask.globals import _request_ctx_stack

from rdflib.namespace import *
from rdflib.term import _LOGGER

from .rule import HeadersRule, URIRefRule, ResourceMap
from . import aggregation
from ldp.resource import Resource
from ldp.globals import _resource_ctx_stack

_LOGGER.setLevel(logging.ERROR)


class LDPApp(Flask):
    url_rule_class = HeadersRule
    resource_rule_class = URIRefRule
    resource_app_class = Resource

    def __init__(self, *args, **kwargs):
        super(LDPApp, self).__init__(*args, **kwargs)
        self.resource_map = ResourceMap()
        self.resource_view_functions = {}

    def create_url_adapter(self, request):
        adapter = super(LDPApp, self).create_url_adapter(request)
        if request is not None:
            for rule in adapter.map._rules:
                rule.headers = request.headers

            def match(self, *args, **kwargs):
                rv = adapter.match(*args, **kwargs)
                for rule in adapter.map._rules:
                    del rules.__dict__['headers']
                return rv
            adapter.match = adapter.match.__get__(adapter, adapter.__class__)
        return adapter

    def add_resource_rule(self,
                          rule,
                          varname,
                          endpoint,
                          view_func,
                          context,
                          **options):
        if endpoint is None:
            endpoint = _endpoint_from_view_func(view_func)

        rule = self.resource_rule_class(rule,
                                        varname,
                                        endpoint,
                                        context,
                                        self.resource_map,
                                        **options)

        self.resource_map.add(rule)
        if view_func is not None:
            old_func = self.resource_view_functions.get(endpoint)
            if old_func is not None and old_func != view_func:
                raise AssertionError('View function mapping is overwriting an '
                                     'existing endpoint function: %s'
                                     % endpoint)
            self.resource_view_functions[endpoint] = view_func

    def resource(self, varname, rule, c=aggregation, **options):
        def decorator(view_func):

            endpoint = options.pop('endpoint', None)
            self.add_resource_rule(
                rule, varname, endpoint, view_func, c, **options)
            return view_func
        return decorator

    def dispatch_request(self):
        req = _request_ctx_stack.top.request
        if req.routing_exception is not None:
            self.raise_routing_exception(req)

        adapter = self.resource_app_class.\
            resolve_resource_app(self.resource_map, req)
        if adapter is None:
            return super(LDPApp, self).dispatch_request()

        resource, resource_app = adapter
        _resource_ctx_stack.push(resource)
        with resource_app.request_context(req.environ):
            return resource_app.full_dispatch_request()
        _resource_ctx_stack.pop()

        #TODO: move this this code to self.resource_adapter

        # if view is bound to resource rule but arguments list
        # parsed by url_adapter is not suitable = raise 404
        self.raise_routing_exception(req)

    def resource_view(self, request, rule, resource, args):
        pass

    def create_resource_adapter(self, map):
        ''' resolves rule
            obtains resource for matched rule
            creates standalone graph resource
            if no cached version available
        '''
        pass
