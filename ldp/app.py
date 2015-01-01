from inspect import getargspec
from types import GeneratorType
from itertools import chain
import os
from zlib import adler32

from werkzeug.http import parse_set_header, generate_etag, HeaderSet
from werkzeug.routing import NotFound
from werkzeug.exceptions import PreconditionFailed

from flask import Flask, request, current_app, g
from flask.globals import _request_ctx_stack
from flask import template_rendered

from ldp.globals import _dataset_ctx_stack
from ldp.dataset import (_push_dataset_ctx,
                         _pop_dataset_ctx)
from ldp.rule import (header_rule_mixin,
                      BindableRule,
                      ResourceContextAdapter)
from ldp.binding import URIRefBinding

from ldp.resource import (implied_types,
                          LDP_BUILDERS_ORDER,
                          LDP_RULE_BUILDERS,
                          MIME_FORMAT)
from ldp import NS


def resource_link_type(response):
    link = parse_set_header(response.headers.get('Link', ''))

    if request.url_rule is None:
        return response

    if request.url_rule.parent:
        link.update(('%s;rel=type' % t
                     for t in request.url_rule.parent.resource_types))
    elif request.url_rule in\
        [getattr(r, 'parent', None) for r
         in current_app.url_map._rules]:
            link.update(('%s;rel=type' % t
                         for t in (NS.NonRDFSource, NS.Resource)))

    response.headers['Link'] = link.to_header()
    return response


def parse_dataset(*args, **kwargs):
    app = current_app._get_current_object()
    if 'DATASET' in app.config:
        return
    descriptors = app.config.get('DATASET_DESCRIPTORS', None)
    if descriptors is not None:
        app.config['DATASET'] = _push_dataset_ctx(**descriptors)
        _pop_dataset_ctx()


def push_default_dataset(*args, **kwargs):
    app = current_app._get_current_object()
    if 'DATASET' in app.config:
        _dataset_ctx_stack.push(app.config['DATASET'])


def pop_default_dataset(response):
    app = current_app._get_current_object()
    if 'DATASET' in app.config:
        _dataset_ctx_stack.pop()
    return response


def aggregated_etag(request):
    if request.url_rule is None:
        return

    if not hasattr(request, 'resource_adapters'):
        return
    
    resources = [a.resource \
                    for a 
                    in sorted(set(request.resource_adapters.values()),
                              key=lambda a:a.resource.identifier)]
    return generate_etag(''.join(r.etag for r in resources).encode('ascii'))


def set_etag(response):
    etag = aggregated_etag(request)

    if etag is not None:
        response.headers['ETag'] = etag

    return response


class LDP(header_rule_mixin(Flask), Flask):
    url_rule_class = BindableRule
    resource_adapter_class = ResourceContextAdapter

    def __init__(self, *args, **kwargs):
        super(LDP, self).__init__(*args, **kwargs)
        self.define_signals()

    def define_signals(self):
        self.before_first_request(parse_dataset)
        self.before_request(push_default_dataset)
        self.after_request(pop_default_dataset)
        self.after_request(resource_link_type)
        self.after_request(set_etag)

    def bind(self, varname, rule, **options):
        def decorator(view_func):
            if isinstance(view_func, tuple):
                view_func, bindings = view_func
            else:
                bindings = []
            bindings.append((varname, rule, options))
            return view_func, bindings
        return decorator

    def route(self, rule, **options):
        def decorator(view_func):
            if isinstance(view_func, tuple):
                view_func, resource_bindings = view_func
            else:
                resource_bindings = []
            endpoint = options.pop('endpoint', None)

            self.add_url_rule(rule, endpoint, view_func, **options)
            if resource_bindings:
                parent = self.url_map._rules.pop()
                for (ldp_rule_args, ldp_options)\
                    in self.ldp_resource_rules(parent,
                                               view_func,
                                               resource_bindings):
                    self.add_url_rule(*ldp_rule_args,
                                      **ldp_options)
                self.url_map._rules.append(parent)
            return view_func, resource_bindings
        return decorator

    def ldp_resource_rules(self, parent, parent_view, bindings):
        argspec = getargspec(parent_view)
        rvars = parent.resource_vars
        for (varname, rule, options) in bindings:
            if varname in rvars:
                raise AssertionError(
                    'Resource mapping var %r:%r overwriting %r' %
                    (varname, rule, rvars[varname].rule))

            if not argspec.varargs and not argspec.keywords:
                if varname not in argspec.args:
                    raise AssertionError(
                        'Resource mapping %r:%r not mappable to function %s' %
                        (varname, rule, parent_view))

            resource_binding = URIRefBinding(rule, self.url_map, **options)

            if not parent.arguments.issuperset(resource_binding.arguments):
                raise AssertionError(
                    'Resource mapping %r:%r cant be formatted with rule %s' %
                                    (varname, rule, parent.rule))

            rvars[varname] = resource_binding

        parent.primary_resource = varname
        parent.resource_types = list(implied_types(
            *options.get('types',
                         parent.default_resource_types)))
        for builder in self.\
                resource_rule_builders(types=parent.resource_types):
            rule_getter = builder(self, parent)
            if isinstance(rule_getter, GeneratorType):
                for ruledef in rule_getter:
                    yield ruledef
            elif rule_getter is not None:
                yield rule_getter

    def resource_rule_builders(self, types=LDP_BUILDERS_ORDER):
        return chain(*(LDP_RULE_BUILDERS.get(ldp_type, [])
                       for ldp_type in types))

    def dispatch_request(self):
        req = _request_ctx_stack.top.request

        if req.routing_exception is not None:
            self.raise_routing_exception(req)

        if req.url_rule.parent is not None:
            rule = req.url_rule.parent
        else:
            rule = req.url_rule

        rvars = rule.resource_vars
        resource_varnames = list(rule.resource_vars.keys())

        req.resource_adapters = {}
        for varname, value in req.view_args.items():
            if varname in rvars:
                req.resource_adapters[varname] = \
                    self.resource_adapter_class(rvars[varname],
                                                req.view_args[varname],
                                                req.url_rule.context,
                                                req.url_rule.pool,
                                                req.url_rule.selectors)
                if req.url_rule.parent and varname == req.url_rule.parent.primary_resource:
                    req.resource_adapters['resource'] = req.resource_adapters[varname]

        for varname in req.resource_adapters:
            resource = req.resource_adapters[varname].resource
            if resource is None and req.method is not 'PUT':
                raise NotFound('Resource %s' % req.view_args[varname])
            req.view_args[varname] = resource
        if 'If-Match' in req.headers:
            if req.headers['If-Match'] != aggregated_etag(req):
                req.routing_exception = PreconditionFailed('Resource changed')
                self.raise_routing_exception(req)
        return super(LDP, self).dispatch_request()

    def make_default_options_response(self, *args, **kwargs):
        '''
        Add `Accept-Patch` headers to default options
        '''
        response = super(LDP,
                         self).make_default_options_response(*args, **kwargs)
        if 'PATCH' in response.allow:
            header = parse_set_header(response.headers.get('Accept-Patch', ''))
            header.update(MIME_FORMAT.keys())
            response.headers['Accept-Patch'] = header
        return response
