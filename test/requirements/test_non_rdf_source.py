"""
### 4.4 Non-RDF Source

The following section contains normative clauses for Linked Data Platform Non-
RDF Source.

#### 4.4.1 General

##### 4.4.1.1 Each LDP Non-RDF Source _MUST_ also be a conforming LDP Resource
in section 4.2 Resource. LDP Non-RDF Sources may not be able to fully express
their state using RDF [rdf11-concepts].

##### 4.4.1.2 LDP servers exposing an LDP Non-RDF Source _MAY_ advertise this
by exposing a HTTP `Link` header with a target URI of
`http://www.w3.org/ns/ldp#NonRDFSource`, and a link relation type of `type`
(that is, `rel='type'`) in responses to requests made to the LDP-NR's HTTP
`Request-URI` [RFC5988].

  *[LDPRs]: Linked Data Platform Resources
  *[LDPR]: Linked Data Platform Resource
  *[LDPC]: Linked Data Platform Container
  *[LDP-RS]: Linked Data Platform RDF Source
  *[RDF]: Resource Description Framework
  *[LDP-NR]: Linked Data Platform Non-RDF Source
"""
from test.requirements.base import LdpTestCase


class LdpnrGeneral(LdpTestCase):

    def test_4_4_1_1(self):
        """
        4.4.1.1 Each LDP Non-RDF Source MUST also be 
a conforming LDP Resource in section 4.2 Resource.  
LDP Non-RDF Sources may not be able to fully express their
state using RDF [rdf11-concepts]. 
        """
        pass