from itertools import chain
from collections import OrderedDict
from functools import wraps
from threading import Lock
from werkzeug.routing import Map, parse_rule, parse_converter_args
import re
from flask import (Blueprint, Flask, request, current_app, g)
from flask.ext.negotiation import provides
from flask.templating import _default_template_ctx_processor
from rdflib import Graph
from rdflib.namespace import RDF
from treelib import Tree, Node


from ldp import NS as LDP
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
    return h

TYPES = ldp_types_hierarchy()


def subclasslist(base):
    subs = (subclasslist(sub) for sub in base.__subclasses__())
    return [base, ] + list(chain(*subs))


def resource_builder(tree, node, *args, debug=True, **kwargs):
    '''
    Maps rdflib.Resource to ldp.Resource app
    '''
    resource_types = [r.identifier for r
                      in node.data.objects(RDF.type)
                      if r.identifier.startswith(LDP)]

    app = get_resource_class(*resource_types)(node, *args, **kwargs)

    app.debug = debug

    app.logger.debug('Built %s' % app)

    return app


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
        for implicit_type in hierarchy.rsearch(explicit_type):
            if implicit_type not in explicit_types:
                if implicit_type not in implicit_types:
                    yield implicit_type
                    implicit_types.append(implicit_type)




class Resource(Flask):
    ldp_type = LDP.Resource
    url_rule_class = HeadersRule
    def __init__(self, node, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.node = node

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


class RDFSource(Resource):
    ldp_type = LDP.RDFSource


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
