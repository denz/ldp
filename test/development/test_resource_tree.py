import unittest
import rdflib
from rdflib.namespace import *
from rdflib.resource import Resource
from ldp.tree import TreeRootsNormalizer
from ldp.url import URL
from ldp import NS as LDP
normalized = TreeRootsNormalizer(RDF.type, FOAF.Person)


class TestResourceTreeBuilder(unittest.TestCase):

    def setUp(self):
        print()
        self.graph = rdflib.Graph()
        self.graph.parse("test/alice.turtle", format='turtle')

    def test_roots_added(self):
        root_url = 'http://example.org'        

        root_ref = rdflib.URIRef(root_url)
        self.graph.add((root_ref, RDF.type, LDP.Resource))
        root_resource = Resource(self.graph, root_ref)
        tree = normalized.tree(self.graph, root_resource)
        tree.show(idhidden=False)
        expected_roots = set(['/'.join((root_url, name)).strip()
                              for name in ('alice', 'bob', 'den')] + ['http://example.org',])
        actual_roots = set(str(item) for item in tree.expand_tree())
        self.assertEqual(expected_roots, actual_roots)
