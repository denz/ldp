from base64 import b64encode, b64decode
from unittest import TestCase

from cached_property import cached_property

from rdflib import Namespace, URIRef

from werkzeug.routing import BaseConverter

from ldp import LDP


CONTINENTS = Namespace('http://www.telegraphis.net/data/continents/')
GN = Namespace('http://www.geonames.org/ontology#')
CAPITALS = Namespace('http://www.telegraphis.net/data/capitals/')
UNKNOWN = URIRef('xxx')
AF = URIRef('http://www.telegraphis.net/data/continents/AF#AF')
AS = URIRef('http://www.telegraphis.net/data/continents/AS#AS')


PUT = '''@prefix dc: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix gn: <http://www.geonames.org/ontology#> .
@prefix geographis: <http://www.telegraphis.net/ontology/geography/geography#> .

<http://www.telegraphis.net/data/continents/{0}#{0}> a geographis:Continent;
    foaf:primaryTopic <#me> ;
    gn:population "922011001" ;
    dc:title "Alice’s FOAF file" .
'''


class B64Converter(BaseConverter):

    def to_python(self, value):
        return b64decode(value).decode()

    def to_url(self, value):
        return b64encode(value).decode()


class LDPTest(TestCase):
    @cached_property
    def app(self):
        app = LDP(__name__)

        class CONFIG:
            DEBUG = True
            DATASET_DESCRIPTORS = getattr(self, 'DATASET_DESCRIPTORS', None)

        app.config.from_object(CONFIG)
        app.url_map.converters['b64'] = B64Converter
        return app

    @property
    def client(self):
        return self.app.test_client()

    def tearDown(self):
        if 'app' in self.__dict__:
            del self.__dict__['app']
