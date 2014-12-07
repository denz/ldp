'''
Test docs
'''
__all__ = ('Ldp', 'NS')
from rdflib.namespace import Namespace
NS = Namespace('http://www.w3.org/ns/ldp#')

from .resource import resource_builder as resource
from .globals import dataset, data, aggregation
from .app import LDPApp