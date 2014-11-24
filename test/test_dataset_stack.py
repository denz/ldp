from unittest import TestCase
from rdflib import URIRef, RDF

from ldp.dataset import context as ds_context
from ldp import data, scheme, ds, NS as LDP


class TestDSStack(TestCase):

    def test_ds_creation(self):
        with ds_context({'id': URIRef('http://example.org/'),
                         'name': 'data',
                         'path': 'test/alice.turtle'},
                        {'name': 'scheme',
                         'id': URIRef(LDP)}):
            # scheme.add((URIRef('http://example.org/'), RDF.type, LDP.Resource))
            # print(ds.serialize(format='turtle').decode())
            # print(scheme.serialize(format='turtle').decode())
            pass
