from rdflib import URIRef

from ldp.globals import pool

from test.base import LDPTest, CONTINENTS, PUT


class TestResourcePool(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    def test_resource_moved_on_get(self):

        @self.app.route('/x/<continent>')
        @self.app.bind('continent',
                       CONTINENTS['<continent>#<continent>'])
        def c0(continent):
            return '%s' % len(list(r.identifier for r in pool.contexts()))

        OC = URIRef(CONTINENTS['OC#OC'])

        self.assertEqual(int(self.client.get('/x/AF').data), 2)
        self.assertTrue(list(self.app.config['DATASET'].g['continents'][OC::]))

        self.assertEqual(int(self.client.get('/x/OC').data), 3)
        self.assertFalse(list(self.app.config['DATASET']
                              .g['continents'][OC::]))

    def test_resource_moved_on_put(self):
        @self.app.route('/x/<continent>')
        @self.app.bind('continent',
                       CONTINENTS['<continent>#<continent>'])
        def c0(continent):
            return '%s' % len(list(r.identifier for r in pool.contexts()))

        OC = URIRef(CONTINENTS['OC#OC'])

        self.client.open('/x/OC',
                         data=PUT.format('OC'),
                         method='PUT',
                         headers={'Content-Type': 'text/turtle'})

        self.assertFalse(list(self.app.config['DATASET']
                              .g['continents'][OC::]))

        self.assertTrue(len([r.identifier for
                             r in self.app.config['DATASET']
                            .g['pool'].contexts()]) > 1)
