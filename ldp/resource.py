from itertools import chain
from collections import OrderedDict
from functools import wraps
from threading import Lock
from werkzeug.routing import Map
import re
from flask import (Blueprint, Flask, request, current_app, g)
from flask.ext.negotiation import provides
from flask.templating import _default_template_ctx_processor
from rdflib import Graph
from rdflib.namespace import RDF
from treelib import Tree, Node


from ldp import NS as LDP, resource as r
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


class Resource(Flask):
    ldp_type = LDP.Resource

    url_rule_class = HeadersRule

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

    def build(self):
        @self.after_request
        def set_ldp_link_types(response):
            response.headers['Link'] = '\t,'.join(('<%s>; rel="type"' % r_type
                                                   for r_type in implied_types(self.ldp_type)))
            return response


class RDFSource(Resource):
    ldp_type = LDP.RDFSource

    def serialize_resource(self, *args, **kwargs):
        g = Graph()
        for (p, o) in r.graph[r.identifier::]:
            g.set((r.identifier, p, o))
        return g.serialize(*args, **kwargs)

    def build(self):

        super(RDFSource, self).build()


        @self.route(match_headers('/<path:path>',
                                  Accept='application/ld+json'),
                                  methods=('GET',))
        def ldjson(path):
            return self.serialize_resource(format='json-ld')

        @self.route('/<path:path>', methods=('GET',))
        def default(path):
            return self.serialize_resource(format='turtle')


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
