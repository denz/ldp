import unittest
from base import LdpTest
from ldp import NS as LDP
from ldp.resource import implied_types
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

    def test_append_implied_types(self):
        self.assertEqual(set(implied_types(LDP.BasicContainer)),
                         set([  LDP.Resource,
                                LDP.Container,
                                LDP.RDFSource,]))