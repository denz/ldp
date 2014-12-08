'''
Test docs
'''
__all__ = ('Ldp', 'NS')
from rdflib.namespace import Namespace
NS = Namespace('http://www.w3.org/ns/ldp#')

from .globals import dataset, data, aggregation, resource
from .app import LDPApp