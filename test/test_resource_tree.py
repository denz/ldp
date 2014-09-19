import unittest
import rdflib
from rdflib.namespace import *
from ldp.tree import TreeRootsNormalizer

normalized = TreeRootsNormalizer(RDF.type, FOAF.Person)


class TestResourceTreeBuilder(unittest.TestCase):

    def setUp(self):
        print()
        self.graph = rdflib.Graph()
        self.graph.parse("test/alice.turtle", format='turtle')

    def test_of_test(self):
        tree = normalized.tree(self.graph, 'example.org')
        tree.show()
