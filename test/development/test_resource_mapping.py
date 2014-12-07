from unittest import TestCase
import re
from rdflib import URIRef, Literal
from rdflib.namespace import *
from rdflib.resource import Resource

from werkzeug.routing import Map
from flask.helpers import locked_cached_property as cached_property

from ldp.url import URL
from ldp import NS as LDP, LDPApp
from ldp.rule import with_context as rmap, URIRefRule
from ldp.globals import continents
from ldp.dataset import _push_dataset_ctx, _pop_dataset_ctx

CONTINENTS = Namespace('http://www.telegraphis.net/data/continents/')
CAPITALS = Namespace('http://www.telegraphis.net/data/capitals/')
GN = Namespace('http://www.geonames.org/ontology#')
from ldp.dataset import context as dataset, NamedContextDataset

AFRICA = URIRef('http://www.telegraphis.net/data/continents/AF#AF')
app = LDPApp(__name__)


class CONFIG:
    GRAPHS = {'continents': {'source': 'test/continents.rdf',
                             'publicID': CONTINENTS},
              'capitails': {'source': 'test/capitals.rdf',
                            'publicID': CAPITALS}
              }
    DEBUG = True

app.config.from_object(CONFIG)


@app.route('/value/<v>')
def index(v):
    return 'value%s'%v


@app.route('/population/<continent>')
@app.resource('continent', CONTINENTS['{continent}#{continent}'], c=continents)
def continent(continent):
    return continent.value(GN.population)


@app.before_request
def before_request():
    _push_dataset_ctx(**app.config['GRAPHS'])


@app.teardown_request
def teardown_request(exception):
    _pop_dataset_ctx()


class TestURIRefRule(TestCase):

    @cached_property
    def ds(self):
        ds = NamedContextDataset()

        ds.g['continents'] = ds.parse(source='test/continents.rdf',
                                      publicID=CONTINENTS)
        ds.g['capitals'] = ds.parse(source='test/capitals.rdf',
                                    publicID=CAPITALS)
        return ds

    def setUp(self):
        self.app = app.test_client()

    def test_formatting(self):

        rule = URIRefRule('http://www.telegraphis.net/data/continents/<code>#<code>',
                          'code',
                          'xxx',
                          self.ds.g['continents'],
                          Map())
        r = rule.resource(code='AF')
        self.assertIn(Literal('Africa', lang='en'), r[GN.name])
        r = rule.resource(code='XX')
        self.assertFalse(list(r[GN.name]))

    def test_url_mapping(self):
        self.assertEqual(self.app.get('/population/AF').data, b'922011000')
        self.assertEqual(self.app.get('/value/x').data, b'valuex')

    def ztest_match(self):
        self.assertEqual(rule.match(AFRICA).value(GN.name),
                         self.ds.g['continents'].resource(AFRICA).value(GN.name))

        self.assertEqual(rule.match('http://www.telegraphis.net/data/continents/AF#EU'),
                         None)
