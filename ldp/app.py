from functools import wraps
import logging
from inspect import getfullargspec as getargspec

from werkzeug.routing import Map, Rule
from werkzeug.exceptions import NotFound
from flask import Flask
from flask.helpers import _endpoint_from_view_func
from flask.globals import _request_ctx_stack


from rdflib.term import _LOGGER
_LOGGER.setLevel(logging.ERROR)

from .rule import HeadersRule, URIRefRule, ResourceMap
from . import aggregation


class LDPApp(Flask):
    url_rule_class = HeadersRule
    resource_rule_class = URIRefRule

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

    def add_resource_rule(self, rule, varname, endpoint, view_func, context, **options):
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
                                     'existing endpoint function: %s' % endpoint)
            self.resource_view_functions[endpoint] = view_func

    def resource(self, varname, rule, c=aggregation, **options):
        def decorator(view_func):

            endpoint = options.pop('endpoint', None)
            self.add_resource_rule(rule, varname, endpoint, view_func, c, **options)
            return view_func
        return decorator


    def dispatch_request(self):
        req = _request_ctx_stack.top.request
        if req.routing_exception is not None:
            self.raise_routing_exception(req)
        rule = req.url_rule
        resource_rules = self.resource_map.endpoint_rules(req.endpoint,
                                                          req.view_args)
        # make ordinal dispatching if no resource rule mapped to url
        if resource_rules is None:
            return super(LDPApp, self).dispatch_request()

        for rule in resource_rules:
            args = req.view_args.copy()
            value = rule.resource(**args)
            if value is not None:
                args[rule.varname] = value
                return self.resource_view_functions[rule.endpoint](**args)

        # if view is bound to resource but arguments list 
        # parsed by url_adapter is not suitable = raise 404
        self.raise_routing_exception(req)
            