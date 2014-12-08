from unittest import TestCase
import re
from rdflib import URIRef, Literal
from rdflib.namespace import *


from werkzeug.routing import Map, BuildError
from flask.helpers import locked_cached_property as cached_property, url_for
from flask import app

from ldp.url import URL
from ldp import NS as LDP, LDPApp
from ldp.rule import URIRefRule
from ldp.globals import continents
from ldp.dataset import _push_dataset_ctx, _pop_dataset_ctx
from ldp.helpers import url_for as url_for_resource

CONTINENTS = Namespace('http://www.telegraphis.net/data/continents/')
CAPITALS = Namespace('http://www.telegraphis.net/data/capitals/')
GN = Namespace('http://www.geonames.org/ontology#')
from ldp.dataset import context as dataset, NamedContextDataset

AFRICA = URIRef('http://www.telegraphis.net/data/continents/AF#AF')
ASIA = URIRef('http://www.telegraphis.net/data/continents/AS#AS')
UNKNOWN = URIRef('xxx')

app = LDPApp(__name__)


class CONFIG:
    GRAPHS = {'continents': {'source': 'test/continents.rdf',
                             'publicID': CONTINENTS},
              'capitails': {'source': 'test/capitals.rdf',
                            'publicID': CAPITALS}
              }
    # DEBUG = True

app.config.from_object(CONFIG)


@app.route('/value/<v>')
def index(v):
    return 'value%s'%v


@app.route('/population/<continent>')
@app.resource('continent', CONTINENTS['<continent>#<continent>'], c=continents)
def continent(continent):
    return continent.value(GN.population)

@app.route('/linkasia/<continent>')
@app.resource('continent', CONTINENTS['<continent>#<continent>'], c=continents)
def getasia(continent):
    return '%s sends to %s'%(continent.value(GN.name),
                             url_for_resource(ASIA))

@app.route('/builderror')
def builderror():
    return '%s'%url_for_resource(UNKNOWN)

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

    def test_resource_retrieving(self):
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

    def test_url_for_resource(self):
        response = self.app.get('/linkasia/AF')
        self.assertEqual(response.data, b'Africa sends to /population/AS')
        # with self.assertRaises(BuildError):
        # try:
        #   response = self.app.get('/builderror')
        # except Exception as e:
        #   print([ e])
