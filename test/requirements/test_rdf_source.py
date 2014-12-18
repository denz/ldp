"""
### 4.3 RDF Source

The following section contains normative clauses for Linked Data Platform RDF
Source.

#### 4.3.1 General

##### 4.3.1.1 Each LDP RDF Source _MUST_ also be a conforming LDP Resource as
defined in section 4.2 Resource, along with the restrictions in this section.
LDP clients _MAY_ infer the following triple: one whose subject is the LDP-RS,
whose predicate is `rdf:type`, and whose object is `ldp:Resource`, but there
is no requirement to materialize this triple in the LDP-RS representation.

##### 4.3.1.2 LDP-RSs representations _SHOULD_ have at least one `rdf:type`
set explicitly. This makes the representations much more useful to client
applications that don't support inferencing.

##### 4.3.1.3 The representation of a LDP-RS _MAY_ have an `rdf:type` of
`ldp:RDFSource` for Linked Data Platform RDF Source.

##### 4.3.1.4 LDP servers _MUST_ provide an RDF representation for LDP-RSs.
The HTTP `Request-URI` of the LDP-RS is typically the subject of most triples
in the response.

##### 4.3.1.5 LDP-RSs _SHOULD_ reuse existing vocabularies instead of creating
their own duplicate vocabulary terms. In addition to this general rule, some
specific cases are covered by other conformance rules.

##### 4.3.1.6 LDP-RSs predicates _SHOULD_ use standard vocabularies such as
Dublin Core [DC-TERMS], RDF [rdf11-concepts] and RDF Schema [rdf-schema],
whenever possible.

##### 4.3.1.7 In the absence of special knowledge of the application or
domain, LDP clients _MUST_ assume that any LDP-RS can have multiple `rdf:type`
triples with different objects.

##### 4.3.1.8 In the absence of special knowledge of the application or
domain, LDP clients _MUST_ assume that the `rdf:type` values of a given LDP-RS
can change over time.

##### 4.3.1.9 LDP clients _SHOULD_ always assume that the set of predicates
for a LDP-RS of a particular type at an arbitrary server is open, in the sense
that different resources of the same type may not all have the same set of
predicates in their triples, and the set of predicates that are used in the
state of any one LDP-RS is not limited to any pre-defined set.

##### 4.3.1.10 LDP servers _MUST NOT_ require LDP clients to implement
inferencing in order to recognize the subset of content defined by LDP. Other
specifications built on top of LDP may require clients to implement
inferencing [rdf11-concepts]. The practical implication is that all content
defined by LDP must be explicitly represented, unless noted otherwise within
this document.

##### 4.3.1.11  A LDP client _MUST_ preserve all triples retrieved from a LDP-
RS using HTTP `GET` that it doesn't change whether it understands the
predicates or not, when its intent is to perform an update using HTTP `PUT`.
The use of HTTP `PATCH` instead of HTTP `PUT` for update avoids this burden
for clients [RFC5789].

##### 4.3.1.12  LDP clients _MAY_ provide LDP-defined hints that allow servers
to optimize the content of responses. section 7.2 Preferences on the Prefer
Request Header defines hints that apply to LDP-RSs.

##### 4.3.1.13  LDP clients _MUST_ be capable of processing responses formed
by a LDP server that ignores hints, including LDP-defined hints.

Feature At Risk

The LDP Working Group proposes incorporation of the following clause to make
LDP clients paging aware:

##### 4.3.1.14  LDP clients _SHOULD_ be capable of processing successful HTTP
`GET` responses formed by a LDP server that independently initiated paging,
returning a page of representation instead of full resource representation
[LDP-PAGING].

#### 4.3.2 HTTP GET

##### 4.3.2.1 LDP servers _MUST_ respond with a Turtle representation of the
requested LDP-RS when the request includes an `Accept` header specifying
`text/turtle`, unless HTTP content negotiation _requires_ a different outcome
[turtle].

> _Non-normative note: _ In other words, Turtle must be returned by LDP
servers in the usual case clients would expect (client requests it) as well as
cases where the client requests Turtle or other media type(s), content
negotiation results in a tie, and Turtle is one of the tying media types. For
example, if the `Accept` header lists `text/turtle` as one of several media
types with the highest relative quality factor (`q=` value), LDP servers must
respond with Turtle. HTTP servers in general are not required to resolve ties
in this way, or to support Turtle at all, but LDP servers are. On the other
hand, if Turtle is one of several requested media types, but another media
type the server supports has a higher relative quality factor, standard HTTP
content negotiation rules apply and the server (LDP or not) would not respond
with Turtle.

##### 4.3.2.2 LDP servers _SHOULD_ respond with a `text/turtle` representation
of the requested LDP-RS whenever the `Accept` request header is absent
[turtle].

Feature At Risk

The LDP Working Group proposes incorporation of the following clause requiring
JSON-LD support.

##### 4.3.2.3 LDP servers _MUST_ respond with a `application/ld+json`
representation of the requested LDP-RS when the request includes an `Accept`
header, unless content negotiation or Turtle support _requires_ a different
outcome [JSON-LD].

  *[LDPRs]: Linked Data Platform Resources
  *[LDP-RS]: Linked Data Platform RDF Source
  *[RDF]: Resource Description Framework
  *[LDPR]: Linked Data Platform Resource
  *[LDPC]: Linked Data Platform Container
"""
from test.requirements.base import LdpTestCase


class LdprsGeneral(LdpTestCase):

    def test_4_3_1_1(self):
        """
        4.3.1.1 Each LDP RDF Source MUST also be 
a conforming LDP Resource as defined in section 4.2 Resource, along with the
restrictions in this section. LDP clients MAY infer the following triple: one
whose subject is the LDP-RS, 
whose predicate is rdf:type, 
and whose object is ldp:Resource, 
but there is no requirement to materialize this triple in the LDP-RS representation.
        """
        pass

    def test_4_3_1_2(self):
        """
        4.3.1.2 LDP-RSs representations SHOULD 
have at least one rdf:type
set explicitly.  This makes the representations much more useful to
client applications that don’t support inferencing.
        """
        pass

    def test_4_3_1_4(self):
        """
        4.3.1.4 LDP servers MUST provide an RDF representation for LDP-RSs. 
The HTTP Request-URI of the LDP-RS is typically the subject of most triples in the response.
        """
        pass

    def test_4_3_1_5(self):
        """
        4.3.1.5 LDP-RSs SHOULD reuse existing vocabularies instead of creating
their own duplicate vocabulary terms.  In addition to this general rule, some specific cases are
covered by other conformance rules.
        """
        pass

    def test_4_3_1_6(self):
        """
        4.3.1.6 LDP-RSs predicates SHOULD use standard vocabularies such as Dublin Core
[DC-TERMS], RDF [rdf11-concepts] and RDF Schema [rdf-schema], whenever
possible.
        """
        pass

    def test_4_3_1_7(self):
        """
        4.3.1.7 In the absence of special knowledge of the application or domain, 
LDP clients MUST assume that any LDP-RS can have multiple rdf:type triples with different objects.
        """
        pass

    def test_4_3_1_8(self):
        """
        4.3.1.8 In the absence of special knowledge of the application or domain, 
LDP clients MUST assume that the rdf:type values
of a given LDP-RS can change over time.
        """
        pass

    def test_4_3_1_9(self):
        """
        4.3.1.9 LDP clients SHOULD always assume that the set of predicates for a
LDP-RS of a particular type at an arbitrary server is open, in the
sense that different resources of the same type may not all have the
same set of predicates in their triples, and the set of predicates that
are used in the state of any one LDP-RS is not limited to any pre-defined
set.
        """
        pass

    def test_4_3_1_11(self):
        """
        4.3.1.11 
A LDP client MUST preserve all triples retrieved from a LDP-RS using HTTP GET that
it doesn’t change whether it understands the predicates or not, when
its intent is to perform an update using HTTP PUT.  The use of HTTP
PATCH instead of HTTP PUT for update avoids this burden for clients
[RFC5789].
        """
        pass

    def test_4_3_1_13(self):
        """
        4.3.1.13 
LDP clients MUST 
be capable of processing responses formed by a LDP server that ignores hints,
including LDP-defined hints.
        """
        pass

    def test_4_3_1_14(self):
        """
        4.3.1.14 
LDP clients SHOULD 
be capable of processing successful HTTP GET responses formed by a LDP server
that independently initiated paging, returning a page of representation instead of full resource
representation [LDP-PAGING].
        """
        pass


class LdprsHttpGet(LdpTestCase):

    def test_4_3_2_1(self):
        """
        4.3.2.1 LDP servers MUST 
respond with a Turtle
representation of the requested LDP-RS when
the request includes an Accept header specifying text/turtle, 
unless HTTP content negotiation requires a different outcome 
[turtle].


Non-normative note: 
In other words, Turtle must be returned by LDP servers 
in the usual case clients would expect (client requests it) 
as well as cases where the client requests Turtle or other media type(s), content negotiation results in a tie,
and Turtle is one of the tying media types.
For example, if the Accept header lists text/turtle as one of several media types with the
highest relative quality
factor (q= value), LDP servers must respond with Turtle.
HTTP servers in general are not required to resolve ties in this way, or to support Turtle at all, but
LDP servers are.
On the other hand, if Turtle is one of several requested media types,
but another media type the server supports has a higher relative quality factor,
standard HTTP content negotiation rules apply and the server (LDP or not) would not respond with Turtle.
        """
        pass

    def test_4_3_2_2(self):
        """
        4.3.2.2 LDP servers SHOULD
respond with a text/turtle
representation of the requested LDP-RS whenever 
the Accept request header is absent [turtle].  
        """

        """this is violated since html application lies on top"""
        pass

    def test_4_3_2_3(self):
        """
        4.3.2.3 LDP servers MUST 
respond with a application/ld+json
representation of the requested LDP-RS
when the request includes an Accept header, unless content negotiation 
or Turtle support
requires a different outcome [JSON-LD].
        """
        pass