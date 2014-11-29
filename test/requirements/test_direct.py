"""
### 5.4 Direct

The following section contains normative clauses for Linked Data Platform
Direct Container.

#### 5.4.1 General

##### 5.4.1.1 Each LDP Direct Container _MUST_ also be a conforming LDP
Container in section 5.2 Container along the following restrictions. LDP
clients _MAY_ infer the following triple: whose subject is the LDP Direct
Container, whose predicate is `rdf:type`, and whose object is `ldp:Container`,
but there is no requirement to materialize this triple in the LDP-DC
representation.

##### 5.4.1.2  LDP Direct Containers _SHOULD_ use the `ldp:member` predicate
as a LDPC's membership predicate if there is no obvious predicate from an
application vocabulary to use. The state of a LDPC includes information about
which resources are its members, in the form of membership triples that follow
a consistent pattern. The LDPC's state contains enough information for clients
to discern the membership predicate, the other consistent membership value
used in the container's membership triples (membership-constant-URI), and the
position (subject or object) where those URIs occurs in the membership
triples. Member resources can be any kind of resource identified by a URI,
LDPR or otherwise.

##### 5.4.1.3 Each LDP Direct Container representation _MUST_ contain exactly
one triple whose subject is the LDPC URI, whose predicate is the
`ldp:membershipResource`, and whose object is the LDPC's membership-constant-
URI. Commonly the LDPC's URI is the membership-constant-URI, but LDP does not
require this.

##### 5.4.1.4 Each LDP Direct Container representation _MUST_ contain exactly
one triple whose subject is the LDPC URI, and whose predicate is either
`ldp:hasMemberRelation` or `ldp:isMemberOfRelation`. The object of the triple
is constrained by other sections, such as ldp:hasMemberRelation or
ldp:isMemberOfRelation, based on the membership triple pattern used by the
container.

###### 5.4.1.4.1 LDP Direct Containers whose membership triple pattern is (
membership-constant-URI , membership-predicate , member-derived-URI ) _MUST_
contain exactly one triple whose subject is the LDPC URI, whose predicate is
`ldp:hasMemberRelation`, and whose object is the URI of membership-predicate.

###### 5.4.1.4.2 LDP Direct Containers whose membership triple pattern is (
member-derived-URI , membership-predicate , membership-constant-URI ) _MUST_
contain exactly one triple whose subject is the LDPC URI, whose predicate is
`ldp:isMemberOfRelation`, and whose object is the URI of membership-predicate.

Feature At Risk

The LDP Working Group proposes the REMOVAL of indirect containers, unless more
implementation reports arrive shortly.

If it is removed, ldp:insertedContentRelation will be removed as well; its
only function currently is to distinguish creation behavior between direct and
indirect containers.

##### 5.4.1.5  LDP Direct Containers _MUST_ behave as if they have a ( LDPC
URI, `ldp:insertedContentRelation` , `ldp:MemberSubject` ) triple, but LDP
imposes no requirement to materialize such a triple in the LDP-DC
representation. The value `ldp:MemberSubject` means that the member-derived-
URI is the URI assigned by the server to a document it creates; for example,
if the client POSTs content to a container that causes the container to create
a new LDPR, `ldp:MemberSubject` says that the member-derived-URI is the URI
assigned to the newly created LDPR.

#### 5.4.2 HTTP POST

##### 5.4.2.1  When a successful HTTP `POST` request to a LDPC results in the
creation of a LDPR, the LDPC _MUST_ update its membership triples to reflect
that addition, and the resulting membership triple _MUST_ be consistent with
any LDP-defined predicates it exposes. A LDP Direct Container's membership
triples _MAY_ also be modified via through other means.

#### 5.4.3 HTTP DELETE

##### 5.4.3.1  When a LDPR identified by the object of a membership triple
which was originally created by the LDP-DC is deleted, the LDPC server _MUST_
also remove the corresponding membership triple.

  *[LDPRs]: Linked Data Platform Resources
  *[LDPCs]: Linked Data Platform Containers
  *[LDPR]: Linked Data Platform Resource
  *[LDPC]: Linked Data Platform Container
  *[LDP-RS]: Linked Data Platform RDF Source
  *[RDF]: Resource Description Framework
  *[LDP-DC]: Linked Data Platform Direct Container
  *[LDP-BC]: Linked Data Platform Basic Container
  *[LDP-NR]: Linked Data Platform Non-RDF Source
"""
from test.requirements.base import LdpTestCase


class LdpdcGeneral(LdpTestCase):

    def test_5_4_1_1(self):
        """
        5.4.1.1 Each LDP Direct Container MUST also be 
a conforming LDP Container in section 5.2 Container along the following
restrictions.  LDP clients MAY infer the following triple:
whose subject is the LDP Direct Container, 
whose predicate is rdf:type, 
and whose object is ldp:Container, 
but there is no requirement to materialize this triple in the LDP-DC representation.
        """
        pass

    def test_5_4_1_2(self):
        """
        5.4.1.2 
LDP Direct Containers
SHOULD use the ldp:member predicate as a LDPC's membership predicate
if there is no obvious predicate from an application vocabulary to use.
The state of a LDPC includes information about which
resources are its members, in the form of membership triples that
follow a consistent pattern.  The LDPC's state contains enough information for clients to discern
the membership predicate, the other consistent membership
value used in the container's membership triples (membership-constant-URI), 
and the position (subject or object) where those URIs
occurs in the membership triples.
Member resources can be
any kind of resource identified by a URI, LDPR or otherwise.
        """
        pass

    def test_5_4_1_3(self):
        """
        5.4.1.3 Each LDP Direct Container
representation MUST contain exactly one triple 
whose subject is the LDPC URI, 
whose predicate is the ldp:membershipResource, 
and whose object is the LDPC's membership-constant-URI.
Commonly the LDPC's URI is the membership-constant-URI, but LDP does not require this.
        """
        pass

    def test_5_4_1_4(self):
        """
        5.4.1.4 Each LDP Direct Container
        representation MUST contain exactly one triple 
        whose subject is the LDPC URI, 
        and whose predicate is either ldp:hasMemberRelation or ldp:isMemberOfRelation. 
        The object of the triple is constrained by other sections, such as
        ldp:hasMemberRelation or 
        ldp:isMemberOfRelation, based on the 
        membership triple 
        pattern used by the container.

        
5.4.1.4.1 LDP Direct Containers
        whose membership triple 
        pattern is ( membership-constant-URI , membership-predicate , member-derived-URI ) MUST
        contain exactly one triple
        whose subject is the LDPC URI, 
        whose predicate is ldp:hasMemberRelation, 
        and whose object is the URI of membership-predicate.


        
5.4.1.4.2 LDP Direct Containers
        whose membership triple 
        pattern is ( member-derived-URI , membership-predicate , membership-constant-URI ) MUST
        contain exactly one triple
        whose subject is the LDPC URI, 
        whose predicate is ldp:isMemberOfRelation, 
        and whose object is the URI of membership-predicate.
        """
        pass

    def test_5_4_1_5(self):
        """
        5.4.1.5 
LDP Direct Containers  
MUST behave as if they
have a ( LDPC URI, ldp:insertedContentRelation , ldp:MemberSubject )
triple, but LDP imposes no requirement to materialize such a triple in the LDP-DC representation.
The value ldp:MemberSubject means that the 
member-derived-URI is the URI assigned by the server to a 
document it creates; for example, if the client POSTs content to a container
that causes the container to create a new LDPR, ldp:MemberSubject says
that the member-derived-URI is the URI assigned to the newly created LDPR.
        """
        pass


class LdpdcHttpPost(LdpTestCase):

    def test_5_4_2_1(self):
        """
        5.4.2.1 
When a successful HTTP POST request to a LDPC results in the creation of a LDPR, 
the LDPC MUST update its membership triples to reflect that addition, and the resulting 
membership triple MUST be consistent with any LDP-defined predicates it exposes.
A LDP Direct Container's membership triples MAY also be modified via 
through other means. 
        """
        pass


class LdpdcHttpDelete(LdpTestCase):

    def test_5_4_3_1(self):
        """
        5.4.3.1 
When a LDPR identified by the object of a membership triple which was
originally created by the LDP-DC is deleted, the LDPC server MUST also remove 
the corresponding membership triple.
        """
        pass