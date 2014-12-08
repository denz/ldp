"""
### 5.3 Basic

The following section contains normative clauses for Linked Data Platform
Basic Container.

#### 5.3.1 General

##### 5.3.1.1 Each LDP Basic Container _MUST_ also be a conforming LDP
Container in section 5.2 Container along with the following restrictions in
this section. LDP clients _MAY_ infer the following triple: whose subject is
the LDP Basic Container, whose predicate is `rdf:type`, and whose object is
`ldp:Container`, but there is no requirement to materialize this triple in the
LDP-BC representation.

  *[LDPRs]: Linked Data Platform Resources
  *[LDPCs]: Linked Data Platform Containers
  *[LDPR]: Linked Data Platform Resource
  *[LDPC]: Linked Data Platform Container
  *[LDP-RS]: Linked Data Platform RDF Source
  *[RDF]: Resource Description Framework
  *[LDP-BC]: Linked Data Platform Basic Container
  *[LDP-NR]: Linked Data Platform Non-RDF Source
"""
from test.requirements.base import LdpTestCase


class LdpbcGeneral(LdpTestCase):

    def test_5_3_1_1(self):
        """
        5.3.1.1 Each LDP Basic Container MUST also be 
a conforming LDP Container in section 5.2 Container along with the
following restrictions in this section. LDP clients MAY infer the following triple:
whose subject is the LDP Basic Container, 
whose predicate is rdf:type, 
and whose object is ldp:Container, 
but there is no requirement to materialize this triple in the LDP-BC representation.
        """
        pass