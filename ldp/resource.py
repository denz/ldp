import re
from itertools import chain
from collections import OrderedDict
from functools import wraps
from threading import Lock
from uuid import uuid5 as uuid
from zlib import adler32

from werkzeug.routing import Map
from werkzeug.exceptions import Forbidden, Conflict, PreconditionFailed
from werkzeug.datastructures import HeaderSet

from flask import (Blueprint, Flask, request, current_app, g)
from flask.ext.negotiation import provides
from flask.templating import _default_template_ctx_processor

from rdflib import ConjunctiveGraph
from rdflib.namespace import RDF

from treelib import Tree, Node


from ldp import NS as LDP, resource as r, dataset as ds
from ldp.rule import HeadersRule, match_headers

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
        response = super(Resource, self).make_default_options_response(*args, **kwargs)
        if 'PATCH' in response.allow:
            response.headers['Accept-Patch'] = HeaderSet(self.patch_media_types)
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
            response.headers['Link'] = HeaderSet('%s;rel=type'%t for t in implied_types(self.ldp_type))
            return response

        @self.after_request
        def set_etag(response):
            response.headers['ETag'] = self.get_etag(r)
            return response

        @self.route(match_headers('/<path:url>',
                               **{'Content-Type':'application/ld+json'}),
                                 methods=('PUT',))
        @self.require_authorization
        def replace_from_ldjson(url):
            self.replace_resource(r, data=request.data,
                                 format='json-ld',
                                 publicID=r.identifier)
            return self.make_response(('', 204, ()))

        @self.route(match_headers('/<path:url>',
                               **{'Content-Type':'text/turtle'}),
                                 methods=('PUT',))
        @self.require_authorization
        def replace_from_turtle(url):
            self.replace_resource(r,    data=request.data,
                                        format='turtle',
                                        publicID=r.identifier)
            return self.make_response(('', 204, ()))


    def replace_resource(self, resource, **kwargs):
        g = ConjunctiveGraph()
        g.parse(**kwargs)

        removed = set()
        added = set()

        for s,p,o,c in ds.quads((resource.identifier, None, None, None)):
            if not s == resource.identifier:
                raise Conflict('Cant remove from third party resource %r'%s)

            if self.allowed_to_remove(ds, s, p, o, c):
                removed.add((s, p, o, c))
            else:
                raise Forbidden('You dont have permission to remove %r of %r'%(p,s))

        for s,p,o in g[::]:
            if not s == resource.identifier:
                raise Conflict('Cant add to third party resource %r'%s)
            if self.allowed_to_add(ds, s, p, o, c):
                added.add((s, p, o, c))
            else:
                raise Forbidden('You dont have permission to add %r to %r'%((p,o),s))

        for quad in removed.difference(added):
            ds.remove(quad)

        for quad in added.difference(removed):
            ds.add(quad)

        return self.on_resource_modified(resource)

    def require_authorization(self, view):
        @wraps(view)
        def authorizator(*args, **kwargs):
            return view(*args, **kwargs)

        return authorizator

    def allowed_to_remove(self, ds, s, p, o, c):
        return True

    def allowed_to_add(self, ds, s, p, o, c):
        return True

    def on_resource_modified(self, resource):
        return resource


class RDFSource(Resource):
    ldp_type = LDP.RDFSource

    def serialize_resource(self, *args, **kwargs):
        g = ConjunctiveGraph()
        for (p, o) in r.graph[r.identifier::]:
            g.set((r.identifier, p, o))
        return g.serialize(*args, **kwargs)

    def build(self):

        @self.route(match_headers('/<path:url>',
                                  Accept='application/ld+json'),
                                  methods=('GET',))
        def serialize_to_ldjson(url):
            return (self.serialize_resource(format='json-ld'),
                    200,
                    {'Content-Type':'application/ld+json'})

        @self.route('/<path:url>', methods=('GET',))
        def serialize_to_turtle(url):
            return (self.serialize_resource(format='turtle'),
                    200,
                    {'Content-Type':'text/turtle'})
        
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
