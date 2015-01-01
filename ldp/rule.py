
import re
import fnmatch

from cached_property import cached_property


from werkzeug.routing import (parse_rule,
                              parse_converter_args,
                              RequestAliasRedirect,
                              ValidationError,
                              BuildError)
from werkzeug._compat import iteritems
from werkzeug.local import LocalProxy

from flask import Flask

from ldp import NS as LDP
from ldp.globals import dataset, pool
from ldp.dataset import DatasetGraphAggregation
from ldp.helpers import Pipeline
from ldp.resource import LDP_RDFResource



class match_headers(str):
    __slots__ = ('headers', )

    def __new__(cls, path, **headers):
        ret = str.__new__(cls, path)
        ret.headers = headers
        return ret


class HeadersRule(Flask.url_rule_class):
    '''
    Can match headers and var inside of headers if rule
        defined with `match_headers` metaclass
    '''
    def match(self, *args, **kwargs):
        match = super(HeadersRule, self).match(*args, **kwargs)
        if hasattr(self.rule, 'headers')\
           and not hasattr(self, '_header_rules_compiled'):
            self.rule.headers = dict(
                                    ((k, self.compile_header_rule(v))
                                     for k, v
                                     in self.rule.headers.items()))
            self._header_rules_compiled = True

        if hasattr(self, 'headers')\
           and hasattr(self.rule, 'headers') and match is not None:
            if not set(self.headers.keys())\
                    .issuperset(set(self.rule.headers.keys())):
                return None

            for header in self.rule.headers:
                header_match = self.rule.headers[
                    header].search(self.headers[header])
                if not header_match:
                    return None
                groups = header_match.groupdict()
                result = {}
                for name, value in iteritems(groups):
                    try:
                        value = self._converters[name].to_python(value)
                    except ValidationError:
                        return
                    result[str(name)] = value
                if self.defaults:
                    result.update(self.defaults)

                if self.alias and self.map.redirect_defaults:
                    raise RequestAliasRedirect(result)
                match.update(result)
        return match

    def compile_header_rule(self, rule):
        """Compiles the regular expression and stores it."""
        assert self.map is not None, 'rule not bound'
        if not '_trace' in self.__dict__:
            self._trace = []
        if not '_converters' in self.__dict__:
            self._converters = {}
        if not '_weights' in self.__dict__:
            self._weights = []
        if not 'arguments' in self.__dict__:
            self.arguments = set()
        regex_parts = []

        def _build_regex(rule):
            for converter, arguments, variable in parse_rule(rule):
                if converter is None:
                    regex_parts.append(fnmatch.translate(variable)[:-7])
                    self._trace.append((False, variable))
                    for part in variable.split('/'):
                        if part:
                            self._weights.append((0, -len(part)))
                else:
                    if arguments:
                        c_args, c_kwargs = parse_converter_args(arguments)
                    else:
                        c_args = ()
                        c_kwargs = {}
                    convobj = self.get_converter(
                        variable, converter, c_args, c_kwargs)
                    regex_parts.append(
                        '(?P<%s>%s)' % (variable, convobj.regex))
                    self._converters[variable] = convobj
                    self._trace.append((True, variable))
                    self._weights.append((1, convobj.weight))
                    self.arguments.add(str(variable))

        # _build_regex(domain_rule)
        # regex_parts.append('\\|')
        self._trace.append((False, '|'))
        _build_regex(rule)
        self._trace.append((False, '/'))
        regex = r'^%s$' % (
            u''.join(regex_parts)
        )
        return re.compile(regex, re.UNICODE)


def header_rule_mixin(cls):
    class HeaderRuleMixin(object):
        def create_url_adapter(self, request):
            adapter = cls.create_url_adapter.__get__(self, cls)(request)
            if request is not None:
                for rule in adapter.map._rules:
                    rule.headers = request.headers
                _match = adapter.match

                def match(self, *args, **kwargs):
                    rv = _match(*args, **kwargs)
                    for rule in adapter.map._rules:
                        del rule.__dict__['headers']
                    return rv
                adapter.match = match.__get__(adapter, adapter.__class__)
            return adapter
    return HeaderRuleMixin


class BindableRule(HeadersRule):
    '''
    Used to create pre rule LDP rules
    '''
    dataset = dataset
    pool = pool
    default_resource_types = [LDP.RDFSource]

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent', None)
        self.pool = kwargs.pop('pool', self.__class__.pool)
        self._context = kwargs.pop('context', self.__class__.dataset)
        self.selectors = kwargs.pop('selectors', [])

        super(BindableRule, self).__init__(*args, **kwargs)
        self.resource_vars = {}

    @cached_property
    def context(self):
        if isinstance(self._context, LocalProxy):
            context = self._context._get_current_object()
        else:
            context = self._context

        if isinstance(context, DatasetGraphAggregation):
            raise TypeError('%r cant be resource context' % context)
        return context

    def match(self, *args, **kwargs):
        match = super(BindableRule, self).match(*args, **kwargs)
        if match is not None:
            if self.parent is not None:
                rvars = self.parent.resource_vars
            else:
                rvars = self.resource_vars
            rv = {}
            for varname in rvars.keys():
                rv[varname] = rvars[varname].uriref(**match)
            match.update(rv)
        return match


def remove_from_context(quad, context, is_quad=True):
    if is_quad:
        context.remove(quad)
    else:
        context.remove(quad[:3])
    return quad


class ResourceContextAdapter(object):
    rdf_resource_class = LDP_RDFResource
    '''
    Resolves rdflib.Resource according to request and rdflib.context
    Moves resource triples to standalone graph into pool if not moved yet
    '''
    resource_quad_selectors = [remove_from_context]

    def __init__(self, binding, uriref, context, pool, selectors):
        self.binding = binding
        self.uriref = uriref
        self.context = context
        self.pool = pool
        self.selectors = selectors + self.resource_quad_selectors

    @cached_property
    def pool_uris(self):
        return [n.identifier for n in self.pool.contexts()]

    @cached_property
    def resource(self):
        if self.uriref in self.pool_uris:
            return self.rdf_resource_class(self.pool.graph(self.uriref),
                                           self.uriref)
        else:
            self.resource_moved_to_pool = False
            g = self.move_to_pool()
            if g is not None:
                return self.rdf_resource_class(g, self.uriref)

    def select_quads(self, quads, context):
        pipeline = Pipeline(self.selectors)

        for q in pipeline(quads, context):
            self.resource_moved_to_pool = True
            yield q

    def move_to_pool(self,):
        g = self.pool.graph(self.uriref)
        for ns in self.context.namespaces():
            g.bind(*ns)
        context = self.context
        if hasattr(context, 'quads'):
            quads = context.quads((self.uriref, None, None, None))

        else:
            quads = ((s, p, o, context.identifier)
                     for s, p, o in context.triples((self.uriref, None, None)))

        for quad in self.select_quads(quads, context):
            self.context.remove(quad)
            g.add(quad[:3])

        if self.resource_moved_to_pool:
            return g

    @cached_property
    def urladapter(self):
        return self.app.create_url_adapter(self.request)

    def url_for(self, uriref):
        for rule in self.map._rules:
            values = rule.match_uriref(uriref)
            if values is not None:
                endpoint = self.map.endpoint_for_rule(rule)
                try:
                    return self.urladapter.build(endpoint, values=values)
                except BuildError as error:
                    self.app.handle_url_build_error(error, endpoint, values)
