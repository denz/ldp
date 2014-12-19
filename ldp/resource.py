import re
from itertools import chain
from collections import OrderedDict
from functools import wraps
from threading import Lock
from uuid import uuid5 as uuid
from zlib import adler32
from pprint import pprint
from copy import copy

from werkzeug.routing import Map
from werkzeug.exceptions import PreconditionFailed
from werkzeug.datastructures import HeaderSet

from flask import (Blueprint, Flask, request, current_app, g)

from rdflib import Graph
from rdflib.namespace import RDF
from rdflib.resource import Resource as RDFResource

from treelib import Tree, Node

from ldp import NS as LDP, resource as r, dataset as ds
from ldp.globals import resources, _dataset_ctx_stack
from ldp.rule import HeadersRule, match_headers
from ldp.helpers import wants_rdfsource, Pipeline
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


def test_removable(triple, resource, request):
    # print('remove', triple)
    yield triple


def test_addable(triple, resource, request):
    # print('add', triple)
    yield triple


class Resource(Flask):
    ldp_type = LDP.Resource
    response_class = LDPResponse
    url_rule_class = HeadersRule
    patch_media_types = ('application/ld+json', 'text/turtle')

    pipelines = {
        'removeable': [],
        'addable': [],
    }

    def create_url_adapter(self, request):
        adapter = super(Resource, self).create_url_adapter(request)
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
            if response.status_code < 400:
                response.headers['ETag'] = self.get_etag(r)
            return response

        def head(url):
            return ''

        self.route(match_headers('/<path:url>',
                                 **{'Accept': 'application/ld+json'}),
                   methods=('HEAD',))(head)

        self.route(match_headers('/<path:url>',
                                 **{'Accept': 'text/turtle'}),
                   methods=('HEAD',))(head)

        def replace_from_ldjson(url):
            self.replace_resource(r, data=request.data,
                                  format='json-ld')
            return self.make_response(('', 204, ()))

        @self.route(match_headers('/<path:url>',
                                  **{'Accept': 'application/ld+json'}),
                    methods=('PUT',))
        def replace_from_ldjson(url):
            self.replace_resource(r, data=request.data,
                                  format='json-ld')
            return self.make_response(('', 204, ()))

        @self.route(match_headers('/<path:url>',
                                  **{'Accept': 'text/turtle'}),
                    methods=('PUT',))
        def replace_from_turtle(url):
            self.replace_resource(r, data=request.data,
                                  format='turtle',)
            return self.make_response(('', 204, ()))

    def get_pipeline(self, name):
        members = copy(self.pipelines.get(name, []))
        members.extend(r.adapter.extra_pipelines.get(name, []))
        return Pipeline(members)

    def replace_resource(self, resource, **kwargs):
        source = Graph()
        source.parse(**kwargs)

        added = set(source[::])
        removed = set(resource.graph[::])

        removeable = self.get_pipeline('removeable')
        addable = self.get_pipeline('addable')
        for triple in removeable(removed.difference(added), r, request):
            resource.graph.remove(triple)

        for triple in addable(added.difference(removed), r, request):
            resource.graph.add(triple)

        for ns in source.namespaces():
            resource.graph.bind(*ns)


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
