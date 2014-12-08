from functools import wraps
from unittest import TestCase

from rdflib import URIRef, Literal
from rdflib.namespace import *

from ldp import LDPApp
from ldp.dataset import _push_dataset_ctx, _pop_dataset_ctx


CONTINENTS = Namespace('http://www.telegraphis.net/data/continents/')
CAPITALS = Namespace('http://www.telegraphis.net/data/capitals/')
GN = Namespace('http://www.geonames.org/ontology#')
AFRICA = URIRef('http://www.telegraphis.net/data/continents/AF#AF')
ASIA = URIRef('http://www.telegraphis.net/data/continents/AS#AS')
UNKNOWN = URIRef('xxx')

app = LDPApp(__name__)

@app.route('/population/<continent>')
@app.resource('continent', CONTINENTS['<continent>#<continent>'])
def continent(continent):
    return continent.value(GN.population)

class CONFIG:
    DEBUG = True

app.config.from_object(CONFIG)

class LdpTestCase(TestCase):
    accept_type = 'text/turtle'

    def setUp(self):
        self.app = app.test_client()
        client_open = self.app.open
        @wraps(client_open)
        def open(client, *args, **kwargs):
            headers = kwargs.pop('headers', {})
            headers['Accept'] = self.accept_type
            kwargs['headers'] = headers
            return client_open(*args, **kwargs)

        self.app.open = open.__get__(self.app, type(self.app))        

        if hasattr(self, 'CONFIG'):
            app.config.from_object(self.CONFIG)

        if hasattr(self, 'GRAPHS'):
            _push_dataset_ctx(**self.GRAPHS)

    def tearDown(self):
        if hasattr(self, 'GRAPHS'):
            _pop_dataset_ctx()

        if hasattr(self, 'CONFIG'):
            app.config.from_object(CONFIG)

