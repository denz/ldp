import re
from itertools import chain
from collections import OrderedDict
from functools import wraps
from threading import Lock
from uuid import uuid5 as uuid
from zlib import adler32
from pprint import pprint

from werkzeug.routing import Map
from werkzeug.exceptions import PreconditionFailed
from werkzeug.datastructures import HeaderSet

from flask import (Blueprint, Flask, request, current_app, g)
from flask.ext.negotiation import provides
from flask.templating import _default_template_ctx_processor

from rdflib import ConjunctiveGraph, Graph
from rdflib.namespace import RDF
from rdflib.resource import Resource as RDFResource

from treelib import Tree, Node

from ldp import NS as LDP, resource as r, dataset as ds
from ldp.globals import resources, _dataset_ctx_stack
from ldp.rule import HeadersRule, match_headers
from ldp.helpers import wants_rdfsource
from ldp.dataset import DatasetGraphAggregation


def ldp_types_hierarchy():
    h = Tree()
    h.create_node(LDP.Resource, LDP.Resource)
    h.create_node(LDP.RDFSource, LDP.RDFSource, LDP.Resource)
    h.create_node(LDP.NonRDFSource, LDP.NonRDFSource, LDP.Resource)
    h.create_node(LDP.Container, LDP.Container, LDP.RDFSource)
    h.create_node(LDP.BasicContainer, LDP.BasicContainer, LDP.Container)
    h.create_node(LDP.DirectContainer, LDP.DirectContainer, LDP.Container)
    h.create_node(LDP.IndirectContainer, LDP.IndirectContainer, LDP.Container)
    l = []

    l.append(LDP.Resource)
    l.append(LDP.RDFSource)
    l.append(LDP.NonRDFSource)
    l.append(LDP.Container)
    l.append(LDP.BasicContainer)
    l.append(LDP.DirectContainer)
    l.append(LDP.IndirectContainer)

    return h, l

TYPES, TYPES_LIST = ldp_types_hierarchy()


def subclasslist(base):
    subs = (subclasslist(sub) for sub in base.__subclasses__())
    return [base, ] + list(chain(*subs))


def get_resource_class(*ldp_types, hierarchy=TYPES):
    resource_types = reversed(subclasslist(Resource))
    deepest_type = max(ldp_types, key=lambda t: hierarchy.level(t))
    for resource_type in resource_types:
        if resource_type.ldp_type == deepest_type:
            return resource_type


def implied_types(*explicit_types, hierarchy=TYPES):
    implicit_types = []
    for explicit_type in explicit_types:
        if not hierarchy.contains(explicit_type):
            continue
        yield explicit_type
        for implicit_type in hierarchy.rsearch(explicit_type):
            if implicit_type not in explicit_types:
                if implicit_type not in implicit_types:
                    yield implicit_type
                    implicit_types.append(implicit_type)


RESOURCE_APPS = {}


def get_resource_app(ldp_types):
    resource_class = get_resource_class(*ldp_types)
    if not resource_class in RESOURCE_APPS:
        app = resource_class(current_app.name)
        app.config.from_object(current_app.config)
        app.build()
        RESOURCE_APPS[resource_class] = app
    return RESOURCE_APPS[resource_class]


class LDPResponse(Flask.response_class):
    default_mimetype = 'application/ld+json; charset=utf-8'


class Resource(Flask):
    ldp_type = LDP.Resource
    response_class = LDPResponse
    url_rule_class = HeadersRule
    patch_media_types = ('application/ld+json', 'text/turtle')
    rdf_resource_class = RDFResource
    rdf_resource_graph_class = Graph
    default_resource_types = [LDP.RDFSource, ]

    @classmethod
    def resolve_resource_app(cls, map, request):
        '''
        match uriref for url
        update args if LDPResource processing is not required and return
        create rdflib.Resource for matched uriref
        move resource triples from dataset to standalone graph
            if that graph not created in ds.g['resources']
        add that graph to ds.g['resources']
        create rdflib.Resource for created graph context or
            take existing from ds.g['resources']
        return None if no resource available
        '''

        resource_rules = map.endpoint_rules(request.endpoint,
                                            request.view_args)
        # make ordinal dispatching if no resource rule mapped to url
        if resource_rules is None:
            return None

        _wants_rdfsource = wants_rdfsource(request)
        args = request.view_args.copy()
        resource = None
        for rule in chain(*resource_rules):
            resource = rule.resource(**request.view_args)
            if resource is not None:
                if not _wants_rdfsource:
                    request.view_args[rule.varname] = resource
                    return
                else:
                    args[rule.varname] = resource
                    break

        if resource is None:
            req.routing_exception = NotFound()
            return

        if resource.identifier not in (n.identifier for n
                                       in resources.contexts()):
            g = resources.graph(resource.identifier)
            moved_triples = False
            for s, p, o, c in rule.quads(resource):
                g.add((s, p, o))
                source = ds.graph(c)
                source.remove((s, p, o))
                moved_triples = True
            if not moved_triples:
                request.routing_exception = NotFound('Resource not found')
                self.raise_routing_exception(request)
            resource = g.resource(resource.identifier)
        else:
            resource = resources.graph(resource.identifier)\
                                .resource(resource.identifier)
        if rule.allow_to_add:
            resource.allow_to_add = rule.allow_to_add.\
                __get__(resource, resource.__class__)

        if rule.allow_to_remove:
            resource.allow_to_remove = rule.allow_to_remove.\
                __get__(resource, resource.__class__)

        ldp_types = [r.identifier for r in resource[
            RDF.type] if r.identifier in TYPES_LIST]

        if not ldp_types:
            ldp_types = cls.default_resource_types
        return resource, get_resource_app(ldp_types)

    def create_url_adapter(self, request):
        adapter = super(Resource, self).create_url_adapter(request)
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

    def make_default_options_response(self, *args, **kwargs):
        '''
        Add `Accept-Patch` headers to default options
        '''
        response = super(Resource,
                         self).make_default_options_response(*args, **kwargs)
        if 'PATCH' in response.allow:
            response.headers['Accept-Patch'] =\
                HeaderSet(self.patch_media_types)
        return response

    def get_etag(self, resource):
        return str(adler32(bytes(resource.identifier, 'utf-8')))

    def build(self):

        @self.before_request
        def check_if_match_etag():
            if 'If-Match' in request.headers:
                if not self.get_etag(r) == request.headers['If-Match']:
                    raise PreconditionFailed('Resource changed')

        @self.after_request
        def set_ldp_link_types(response):
            response.headers['Link'] = \
                HeaderSet('%s;rel=type' % t for t
                          in implied_types(self.ldp_type))
            return response

        @self.after_request
        def set_etag(response):
            response.headers['ETag'] = self.get_etag(r)
            return response

        @self.route(match_headers('/<path:url>',
                                  **{'Content-Type': 'application/ld+json'}),
                    methods=('PUT',))
        @self.require_authorization
        def replace_from_ldjson(url):
            self.replace_resource(r, data=request.data,
                                  format='json-ld')
            return self.make_response(('', 204, ()))

        @self.route(match_headers('/<path:url>',
                                  **{'Content-Type': 'text/turtle'}),
                    methods=('PUT',))
        @self.require_authorization
        def replace_from_turtle(url):
            self.replace_resource(r, data=request.data,
                                  format='turtle',)
            return self.make_response(('', 204, ()))

    def replace_resource(self, resource, **kwargs):
        source = ConjunctiveGraph()
        source.parse(**kwargs)

        removed = set()
        added = set()
        for s, p, o in source[::]:
            if resource.allow_to_add(current_app, s, p, o):
                added.add((s, p, o))

        for s, p, o in resource.graph.triples((None, None, None)):
            if resource.allow_to_remove(current_app, s, p, o):
                removed.add((s, p, o))

        for triple in removed.difference(added):
            resource.graph.remove(triple)

        for triple in added.difference(removed):
            resource.graph.add(triple)

        return self.on_resource_modified(resource)

    def require_authorization(self, view):
        @wraps(view)
        def authorizator(*args, **kwargs):
            return view(*args, **kwargs)

        return authorizator

    def on_resource_modified(self, resource):
        return resource


class RDFSource(Resource):
    ldp_type = LDP.RDFSource

    def build(self):

        @self.route(match_headers('/<path:url>',
                                  Accept='application/ld+json'),
                    methods=('GET',))
        def serialize_to_ldjson(url):
            return (r.graph.serialize(format='json-ld'),
                    200,
                    {'Content-Type': 'application/ld+json'})

        @self.route('/<path:url>', methods=('GET',))
        def serialize_to_turtle(url):
            return (r.graph.serialize(format='turtle'),
                    200,
                    {'Content-Type': 'text/turtle'})

        super(RDFSource, self).build()


class NonRDFSource(Resource):
    ldp_type = LDP.NonRDFSource


class Container(RDFSource):
    ldp_type = LDP.Container


class BasicContainer(Container):
    ldp_type = LDP.BasicContainer


class DirectContainer(Container):
    ldp_type = LDP.DirectContainer


class IndirectContainer(Container):
    ldp_type = LDP.IndirectContainer
