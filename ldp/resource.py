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

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, node):
        self._node = node
        # reset all application if new node set
        self.view_functions = {}
        self._error_handlers = {}
        self.error_handler_spec = {None: self._error_handlers}
        self.url_build_error_handlers = []
        self.before_request_funcs = {}
        self.before_first_request_funcs = []
        self.after_request_funcs = {}
        self.teardown_request_funcs = {}
        self.teardown_appcontext_funcs = []
        self.url_value_preprocessors = {}
        self.url_default_functions = {}
        self.template_context_processors = {
            None: [_default_template_ctx_processor]
        }
        self.blueprints = {}
        self.extensions = {}
        self.url_map = Map()
        self._got_first_request = False
        self._before_request_lock = Lock()
        self.on_node_set()

    def on_node_set(self):
        resource_types = [r.identifier for r
                          in self.node.data.objects(RDF.type)
                          if r.identifier.startswith(LDP)]

        @self.after_request
        def set_ldp_link_types(response):

            response.headers['Link'] = '\t,'.join(('<%s>; rel="type"' % r_type
                                                   for r_type in resource_types))
            return response


class RDFSource(Resource):
    ldp_type = LDP.RDFSource

    def serialize(self, *args, **kwargs):
        r = self.node.data
        g = Graph()
        for (p, o) in r.graph[r.identifier::]:
            g.set((r.identifier, p, o))
        return g.serialize(*args, **kwargs)

    def on_node_set(self):
        super(RDFSource, self).on_node_set()

        @self.route(match_headers('/', Accept='application/*'), methods=('GET',))
        def ldjson():
            return self.serialize(format='turtle')

        @self.route('/', methods=('GET',))
        def default():
            return self.serialize(format='turtle')


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
