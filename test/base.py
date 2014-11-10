from unittest import TestCase
from rdflib import Graph, URIRef
from rdflib.namespace import *
from rdflib.resource import Resource
from flask import Flask
from slugify import slugify

from ldp.app import NestedFlask, NestedFlaskMapping
from ldp.tree import TreeRootsNormalizer
from ldp import resource, NS as LDP
from ldp.resource import implied_types
from ldp.url import URL


def resource_app_constructor(tree, node):
    subs = tree.children(node.identifier)
    # place where we adding LDP types
    # so flask application be mapped to ldp resource type
    for ldp_type in implied_types(LDP.BasicContainer):
        node.data.add(RDF.type, ldp_type)
    node.data.add(RDF.type, LDP.BasicContainer)
    # print(node.data.objects(RDF.type))
    # node.data.add(RDF.type, LDP.IndirectContainer)
    nested = NestedFlask(
        resource(tree, node, slugify(node.identifier)),
        NestedFlaskMapping(tree, subs, resource_app_constructor))
    return nested


class LdpTest(TestCase):
    rdf_source = 'test/alice.turtle'
    resource_app_constructor = staticmethod(resource_app_constructor)
    normalized = TreeRootsNormalizer(RDF.type, FOAF.Person)
    hostname = 'example.org'

    def setUp(self):
        print()
        self.graph = Graph()
        self.graph.parse("test/alice.turtle", format='turtle')

        root_ref = URIRef(URL('')(scheme='http', netloc=self.hostname, path='/'))
        self.graph.add((root_ref, RDF.type, LDP.RDFSource))
        root_resource = Resource(self.graph, root_ref)
        for ldp_type in implied_types(LDP.RDFSource):
            root_resource.add(RDF.type, ldp_type)
        root_id = root_resource.identifier
        self.tree = self.normalized.tree(self.graph, root_resource)

        root = self.tree.get_node(root_id)
        subs = self.tree.children(root_id)


        self.app = NestedFlask(
            resource(self.tree, root, slugify(root.identifier)),
            NestedFlaskMapping(self.tree,
                               subs,
                               self.resource_app_constructor))

        self.c = self.app.test_client()

    def urls(self):
        _urls = []
        for path in self.tree.paths_to_leaves():
            path = [self.tree.get_node(nid).tag for nid in path]
            for i in range(len(path)):
                url = ''.join(path[1:i + 1])
                if not url in _urls:
                    _urls.append(url)
        return sorted(_urls)
