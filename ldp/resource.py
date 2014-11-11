from itertools import chain
from collections import OrderedDict
from functools import wraps
from flask import (Blueprint, Flask, request, current_app, g)
from rdflib import Graph
from rdflib.namespace import RDF
from treelib import Tree, Node


from ldp import NS as LDP

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


def resource_builder(tree, node, *args, debug=False, **kwargs):
    '''
    Maps rdflib.Resource to ldp.Resource app
    '''
    resource_types = [r.identifier for r
                      in node.data.objects(RDF.type)
                      if r.identifier.startswith(LDP)]

    app = Flask(*args, **kwargs)

    app.debug = debug

    @app.after_request
    def set_ldp_link_types(response):

        response.headers['Link'] = '\t,'.join(('<%s>; rel="type"' % r_type
                                               for r_type in resource_types))
        return response

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
