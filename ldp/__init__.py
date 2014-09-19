'''
Test docs
'''
__all__ = ('Ldp', 'NS')
from rdflib.namespace import Namespace
from .app import Ldp
NS = Namespace('http://www.w3.org/ns/ldp#')