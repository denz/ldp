"""
### 5.5 Indirect

Feature At Risk

The LDP Working Group proposes the REMOVAL of indirect containers, unless more
implementation reports arrive shortly.

The following section contains normative clauses for Linked Data Platform
Indirect Container.

#### 5.5.1 General

##### 5.5.1.1 Each LDP Indirect Container _MUST_ also be a conforming LDP
Direct Container as described in section 5.4 Direct, along with the following
restrictions. LDP clients _MAY_ infer the following triple: one whose subject
is LDP Indirect Container, whose predicate is `rdf:type`, and whose object is
`ldp:Container`, but there is no requirement to materialize this triple in the
LDP-IC representation.

##### 5.5.1.2  LDP Indirect Containers _MUST_ contain exactly one triple whose
subject is the LDPC URI, whose predicate is `ldp:insertedContentRelation`, and
whose object ICR describes how the member-derived-URI in the container's
membership triples is chosen. The member-derived-URI is taken from some triple
( S, P, O ) in the document supplied by the client as input to the create
request; if ICR's value is P, then the member-derived-URI is O. LDP does not
define the behavior when more than one triple containing the predicate P is
present in the client's input. For example, if the client POSTs RDF content to
a container that causes the container to create a new LDP-RS, and that content
contains the triple ( <> , foaf:primaryTopic , bob#me ) `foaf:primaryTopic`
says that the member-derived-URI is bob#me. One consequence of this definition
is that indirect container member creation is only well-defined by LDP when
the document supplied by the client as input to the create request has an RDF
media type.

#### 5.5.2 HTTP POST

##### 5.5.2.1 LDPCs whose `ldp:insertedContentRelation` triple has an object
**other than** `ldp:MemberSubject` and that create new resources _MUST_ add a
triple to the container whose subject is the container's URI, whose predicate
is `ldp:contains`, and whose object is the newly created resource's URI (which
will be different from the member-derived URI in this case). This
`ldp:contains` triple can be the only link from the container to the newly
created resource in certain cases.

  *[LDPRs]: Linked Data Platform Resources
  *[LDPCs]: Linked Data Platform Containers
  *[LDPR]: Linked Data Platform Resource
  *[LDPC]: Linked Data Platform Container
  *[LDP-IC]: Linked Data Platform Indirect Container
  *[LDP-RS]: Linked Data Platform RDF Source
  *[RDF]: Resource Description Framework
  *[LDP-DC]: Linked Data Platform Direct Container
  *[LDP-BC]: Linked Data Platform Basic Container
  *[LDP-NR]: Linked Data Platform Non-RDF Source
"""
from test.requirements.base import LdpTestCase


class LdpicGeneral(LdpTestCase):

    def test_5_5_1_1(self):
        """
        5.5.1.1 Each LDP Indirect Container MUST also be 
a conforming LDP Direct Container as described in section 5.4 Direct, along with the following
restrictions.  LDP clients MAY infer the following triple: one 
whose subject is LDP Indirect Container, 
whose predicate is rdf:type, 
and whose object is ldp:Container, 
but there is no requirement to materialize this triple in the LDP-IC representation.
        """
        pass

    def test_5_5_1_2(self):
        """
        5.5.1.2 
    LDP Indirect Containers
    MUST contain exactly one triple whose
subject is the LDPC URI, 
    whose predicate is ldp:insertedContentRelation, and 
    whose object ICR describes how the member-derived-URI in 
    the container's membership triples is chosen.
    The member-derived-URI is taken from some triple 
    ( S, P, O ) in the document supplied by the client as input to the create request;
    if ICR's value is P, then the member-derived-URI is
    O.  LDP does not define the behavior when more than one triple containing 
    the predicate P is present in the client's input.
    For example, if the client POSTs RDF content to a container
    that causes the container to create a new LDP-RS, and that content contains the triple 
    ( <> , foaf:primaryTopic , bob#me )
    foaf:primaryTopic says
    that the member-derived-URI is bob#me.  
    One consequence of this definition is that indirect container member creation is only 
    well-defined by LDP when the document supplied by the client as input to the create request
    has an RDF media type.
    
        """
        pass


class LdpicHttpPost(LdpTestCase):

    def test_5_5_2_1(self):
        """
        5.5.2.1 LDPCs 
whose ldp:insertedContentRelation triple has an object
other than ldp:MemberSubject 
and that create new resources 
MUST add a triple to the container
whose subject is the container's URI, 
whose predicate is ldp:contains, and
whose object is the newly created resource's URI (which will be different from
the member-derived URI in this case).
This ldp:contains triple can be the only link from the container to the newly created
resource in certain cases.
        """
        pass