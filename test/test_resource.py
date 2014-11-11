import unittest
from base import LdpTest
from ldp import NS as LDP, ds
from ldp.resource import (implied_types,
                          get_resource_class,
                          BasicContainer,
                          Container,
                          Resource, RDFSource)

class TestResource(LdpTest):

    """
    `http://www.w3.org/TR/ldp/#h3_ldpr-resource`_
    """

    def ztest_options(self):
        for url in self.urls():
            response = self.c.open(url, method='OPTIONS')
            self.assertTrue(response.status_code < 500)

    def test_link_header(self):
        response = self.c.open('http://example.org/')
        self.assertIn(LDP.Resource, response.headers['Link'])
        self.assertIn(LDP.RDFSource, response.headers['Link'])

        for url in ('http://example.org/alice',
                    'http://example.org/den',
                    'http://example.org/alice',):
            response = self.c.open(url)
            self.assertIn(LDP.Resource, response.headers['Link'])
            self.assertIn(LDP.RDFSource, response.headers['Link'])
            self.assertIn(LDP.Container, response.headers['Link'])
            self.assertIn(LDP.BasicContainer, response.headers['Link'])
        print(ds.serialize(format='turtle').decode())

    def ztest_append_implied_types(self):
        self.assertEqual(set(implied_types(LDP.BasicContainer)),
                         set([LDP.Resource,
                              LDP.Container,
                              LDP.RDFSource, ]))

    def test_resource_class_getter(self):
        self.assertEqual(get_resource_class(LDP.Resource,
                                            LDP.RDFSource,
                                            LDP.Container,
                                            LDP.BasicContainer),
                         BasicContainer
                         )
        self.assertEqual(get_resource_class(LDP.Resource,
                                            LDP.RDFSource,
                                            LDP.Container),
                         Container
                         )

        self.assertEqual(get_resource_class(LDP.Resource,
                                            LDP.RDFSource,),
                         RDFSource
                         )

        self.assertEqual(get_resource_class(LDP.Resource,),
                         Resource
                         )
