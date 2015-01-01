from flask import request
from cached_property import cached_property
from treelib import Tree

from werkzeug.http import generate_etag

from rdflib import Graph
from rdflib.resource import Resource as RDFResource

from ldp import NS as LDP
from ldp.helpers import Uncacheable



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

MIME_FORMAT = {'text/turtle': 'turtle',
               'application/ld+json': 'jsonld',
               }


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


class LDP_RDFResource(Uncacheable, RDFResource):
    SERIALIZED_ATTRIBUTE_MAP = {
                                'text/turtle': 'turtle_serialization',
                                'application/ld+json': 'ldjson_serialization',
                               }
    @cached_property
    def etag(self):
        return generate_etag(self.turtle_serialization)

    @cached_property
    def turtle_serialization(self):
        return self.graph.serialize(format='turtle')


    @cached_property
    def ldjson_serialization(self):
        return self.graph.serialize(format='jsonld')

    @cached_property
    def rdfxml_serialization(self):
        return self.graph.serialize()


def replace_resource(rule, resource, **kwargs):
        source = Graph(identifier=resource.identifier)
        source.parse(**kwargs)

        added = set(source[::])
        removed = set(resource.graph[::])

        for triple in removed.difference(added):
            resource.graph.remove(triple)

        for triple in added.difference(removed):
            resource.graph.add(triple)

        for ns in source.namespaces():
            resource.graph.bind(*ns)


def build_put_rule(app, parent):
    from ldp.rule import match_headers    
    def ldp_put(resource, mimetype, **kwargs):
        replace_resource(request.url_rule,
                         resource,
                         data=request.data,
                         format=MIME_FORMAT[mimetype])
        resource.uncache()
        return app.make_response(('', 204, ()))

    rule = match_headers(
        parent.rule,
        **{'Content-Type':
           '<any("application/ld+json","text/turtle"):mimetype>'})

    yield ((rule, parent.endpoint + '.ldp.put', ldp_put),
           {'methods': ('PUT',), 'parent': parent})

def build_get_rule(app, parent):
    from ldp.rule import match_headers    
    def ldp_get(resource, mimetype, **kwargs):
        return app.make_response((getattr(resource,
                                          resource.SERIALIZED_ATTRIBUTE_MAP[mimetype]),
                                  200,
                                  {'Content-Type':mimetype}))

    rule = match_headers(
        parent.rule,
        **{'Accept':
           '<any("application/ld+json","text/turtle"):mimetype>'})

    yield ((rule, parent.endpoint + '.ldp.get', ldp_get),
           {'methods': ('GET',), 'parent': parent})


LDP_BUILDERS_ORDER = [LDP.Resource,
                      LDP.RDFSource,
                      LDP.Container,
                      LDP.BasicContainer]


LDP_RULE_BUILDERS = {
    LDP.Resource: [build_put_rule],
    LDP.RDFSource: [build_get_rule],
}
