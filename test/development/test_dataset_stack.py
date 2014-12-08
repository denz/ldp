from unittest import TestCase
from rdflib import URIRef, RDF, Graph

from ldp import NS as LDP
from ldp.dataset import NamedContextDataset, context as dataset

from ldp.globals import continents, capitals, aggregation

CONTINENTS = URIRef('http://www.telegraphis.net/data/continents')
CAPITALS = URIRef('http://www.telegraphis.net/data/capitals')

class TestNamedContext(TestCase):
    def test_single_context_parse(self):
        ds = NamedContextDataset()

        ds.g['cont'] = ds.parse(source='test/continents.rdf',
                                publicID=CONTINENTS)
        self.assertEqual(len(list(ds.g['cont'][::])), 112)

    def test_multiple_context_parse(self):
        ds = NamedContextDataset()

        ds.g['cont'] = ds.parse(source='test/continents.rdf',
                                publicID=CONTINENTS)
        self.assertEqual(len(list(ds.g['cont'][::])), 112)
        ds.g['capitals'] = ds.parse(source='test/capitals.rdf',
                                    publicID=CONTINENTS)
        self.assertEqual(len(list(ds.g['cont'][::])), 2584)

    def test_multiple_context_aggregation(self):
        ds = NamedContextDataset()

        ds.g['cont'] = ds.parse(source='test/continents.rdf',
                                publicID=CONTINENTS)
        ds.g['capitals'] = ds.parse(source='test/capitals.rdf',
                                    publicID=CAPITALS)
        self.assertEqual(len(list(ds.g.aggregation[::])), 2696)

    def test_graph_context(self):
        with dataset(cont={ 'source':'test/continents.rdf',
                            'publicID':CONTINENTS}) as ds:
            self.assertEqual(len(list(ds.g['cont'][::])), 112)

    def test_globals(self):
        with dataset(continents={'source':'test/continents.rdf',
                    'publicID':CONTINENTS},
                     capitals={'source':'test/capitals.rdf',
                               'publicID':CAPITALS}) as ds:
            self.assertEqual(len(list(continents[::])), 112)
            self.assertEqual(len(list(capitals[::])), 2584)
            self.assertEqual(len(list(aggregation[::])), 2696)