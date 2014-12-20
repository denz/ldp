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
from werkzeug.exceptions import (
    PreconditionFailed, UnprocessableEntity, Conflict)
from werkzeug.datastructures import HeaderSet

from flask import (Blueprint, Flask, request, current_app, g)

from rdflib import Graph
from rdflib.namespace import RDF
from rdflib.resource import Resource as RDFResource

from treelib import Tree, Node

from ldp import NS as LDP, resource as r, dataset as ds
from ldp.globals import resources, _dataset_ctx_stack
from ldp.rule import HeadersRule, match_headers, header_rule_mixin
from ldp.helpers import wants_resource, Pipeline
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


def disable_remove_containment_on_put(triple, resource, request):
    # print('remove', triple)
    yield triple


def disable_add_containment_on_put(triple, resource, request):
    # print('add', triple)
    yield triple


class Resource(header_rule_mixin(Flask), Flask):
    ldp_type = LDP.Resource
    response_class = LDPResponse
    url_rule_class = HeadersRule
    patch_mime_types = ('application/ld+json', 'text/turtle')
    mime_format = {'text/turtle': 'turtle',
                   'application/ld+json': 'json-ld',
                   }

    pipelines = {
        'removeable': [],
        'addable': [],
    }

    def make_default_options_response(self, *args, **kwargs):
        '''
        Add `Accept-Patch` headers to default options
        '''
        response = super(Resource,
                         self).make_default_options_response(*args, **kwargs)
        if 'PATCH' in response.allow:
            response.headers['Accept-Patch'] =\
                HeaderSet(self.patch_mime_types)
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

        @self.route(match_headers('/<path:url>',
                                  Accept='<any("application/ld+json","text/turtle"):mimetype>'),
                    methods=('HEAD',))
        def head(url, mimetype):
            return ''

        @self.route(match_headers('/<path:url>',
                                  **{'Content-Type': '<any("application/ld+json","text/turtle"):mimetype>'}),
                    methods=('PUT',))
        def replace(url, mimetype):
            self.replace_resource(r, data=request.data,
                                  format=self.mime_format[mimetype])
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

    def make_default_options_response(self, *args, **kwargs):
        '''
        Add `Accept-Post` headers to default options
        '''
        response = super(Resource,
                         self).make_default_options_response(*args, **kwargs)
        if 'POST' in response.allow:
            response.headers['Accept-Post'] =\
                HeaderSet(self.post_mime_types)
        return response

    def build(self):
        rule = match_headers('/<path:url>',
                             Accept='<any("application/ld+json","text/turtle"):mimetype>')

        @self.route(rule, methods=('GET',))
        def serialize(url, mimetype):
            return (r.graph.serialize(format=self.mime_format[mimetype]),
                    200,
                    {'Content-Type': mimetype})

        super(RDFSource, self).build()


class NonRDFSource(Resource):
    ldp_type = LDP.NonRDFSource


def deny_modify_containment_on_put(triple, resource, request):
    if triple[1] == LDP.contains and request.method == 'PUT':
        raise Conflict('Unable to modify containment triple for %r'
                       % triple[0])
    yield triple


class Container(RDFSource):
    ldp_type = LDP.Container
    post_mime_types = ('application/ld+json', 'text/turtle')

    pipelines = {
        'removeable': [deny_modify_containment_on_put, ],
        'addable': [deny_modify_containment_on_put, ],
    }

    def build(self):
        @self.route(match_headers('/<path:url>',
                                  **{'Content-Type': '<any("application/ld+json","text/turtle"):mimetype>'}),
                    methods=('POST',))
        def append(url, mimetype):
            path, uriref = self.create_resource(url, r, data=request.data,
                                                format=self.mime_format[mimetype])

            r.add(LDP.contains, uriref)

            return self.make_response(('', 201, (('Location', path), )))

        super(Container, self).build()

    def identified_graph(self, **kwargs):
        g = Graph().parse(**kwargs)
        try:
            next(g[::])
        except StopIteration:
            raise UnprocessableEntity('No triples found in <pre>\n%r\n</pre>' % kwargs['data'].decode())

        subject = list(set((s for s, o in g[:RDF.type:])))
        if len(subject) > 1:
            raise Conflict('Multiple subjects %r found while creating resource' %
                           subject)
        subject = subject.pop()
        if subject in r.adapter.pool:
            raise Conflict('Resource %r alredy exists' % subject)
        return subject, g[::]

    def create_resource(self, url, resource, **kwargs):
        identifier, triples = self.identified_graph(**kwargs)

        link = resource.adapter.url_for(identifier)

        if link is not None:
            dest = resource.adapter.resource_pool.graph(identifier)
            for t in triples:
                dest.add(t)

            return link, dest.identifier
        else:
            raise UnprocessableEntity('No url found for %r' % identifier)


class BasicContainer(Container):
    ldp_type = LDP.BasicContainer


class DirectContainer(Container):
    ldp_type = LDP.DirectContainer


class IndirectContainer(Container):
    ldp_type = LDP.IndirectContainer
