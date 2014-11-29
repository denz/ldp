from unittest import TestCase
from rdflib import Graph, URIRef, Dataset
from rdflib.namespace import *
from rdflib.resource import Resource
from flask import Flask, g
from slugify import slugify

from ldp.app import NestedFlask, NestedFlaskMapping
from ldp.tree import TreeRootsNormalizer
from ldp import resource, NS as LDP, ds, scheme, data
from ldp.dataset import context as ds_context
from ldp.resource import implied_types
from ldp.url import URL
from ldp.globals import _dataset_ctx_stack



def resource_app_constructor(tree, node):
    subs = tree.children(node.identifier)
    # place where we adding LDP types
    # so flask application be mapped to ldp resource type
    data = scheme.resource(node.data._identifier)
    for ldp_type in implied_types(LDP.BasicContainer):    
        data.add(RDF.type, ldp_type)
    data.add(RDF.type, LDP.BasicContainer)
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
        with ds_context({'id': URIRef('http://example.org/'),
                         'name': 'data',
                         'path': 'test/alice.turtle'},
                        {'name': 'scheme',
                         'id': URIRef(LDP)}) as ds:
                            _dataset_ctx_stack.push(ds)
        root_ref = URIRef(
            URL('')(scheme='http', netloc=self.hostname, path='/'))

        scheme.add((root_ref, RDF.type, LDP.RDFSource))

        root_resource = Resource(scheme, root_ref)

        for ldp_type in implied_types(LDP.RDFSource):
            root_resource.add(RDF.type, ldp_type)
        root_id = root_resource.identifier
        self.tree = self.normalized.tree(ds, root_resource)

        root = self.tree.get_node(root_id)
        subs = self.tree.children(root_id)

        self.app = NestedFlask(
            resource(self.tree, root, slugify(root.identifier)),
            NestedFlaskMapping(self.tree,
                               subs,
                               self.resource_app_constructor))

        self.c = self.app.test_client()

    def tearDown(self):
        _dataset_ctx_stack.pop()

    def urls(self):
        _urls = []
        for path in self.tree.paths_to_leaves():
            path = [self.tree.get_node(nid).tag for nid in path]
            for i in range(len(path)):
                url = ''.join(path[1:i + 1])
                if not url in _urls:
                    _urls.append(url)
        return sorted(_urls)
