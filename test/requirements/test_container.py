"""
### 5.2 Container

The following section contains normative clauses for Linked Data Platform
Container.

#### 5.2.1 General

The Linked Data Platform does not define how clients discover LDPCs.

##### 5.2.1.1 Each Linked Data Platform Container _MUST_ also be a conforming
Linked Data Platform RDF Source. LDP clients _MAY_ infer the following triple:
one whose subject is the LDPC, whose predicate is `rdf:type`, and whose object
is `ldp:RDFSource`, but there is no requirement to materialize this triple in
the LDPC representation.

##### 5.2.1.2 The representation of a LDPC _MAY_ have an `rdf:type` of
`ldp:Container` for Linked Data Platform Container. Non-normative note: LDPCs
might have additional types, like any LDP-RS.

##### 5.2.1.3 LDPC representations _SHOULD NOT_ use RDF container types
`rdf:Bag`, `rdf:Seq` or `rdf:List`.

Feature At Risk

The LDP Working Group proposes the REMOVAL of indirect containers, unless more
implementation reports arrive shortly, which would change the contents of the
list below.

##### 5.2.1.4 LDP servers exposing LDPCs _MUST_ advertise their LDP support by
exposing a HTTP `Link` header with a target URI matching the type of container
(see below) the server supports, and a link relation type of `type` (that is,
`rel='type'`) in all responses to requests made to the LDPC's HTTP `Request-
URI`. LDP servers _MAY_ provide additional HTTP `Link: rel='type'` headers.
The notes on the corresponding LDPR constraint apply equally to LDPCs.

> Valid container type URIs for `rel='type'` defined by this document are:

>

>   * `http://www.w3.org/ns/ldp#BasicContainer` \- for LDP Basic Containers

>   * `http://www.w3.org/ns/ldp#DirectContainer` \- for LDP Direct Containers

>   * `http://www.w3.org/ns/ldp#IndirectContainer` \- for LDP Indirect
Containers

##### 5.2.1.5 LDP servers _SHOULD_ respect all of a client's LDP-defined
hints, for example which subsets of LDP-defined state the client is interested
in processing, to influence the set of triples returned in representations of
a LDPC, particularly for large LDPCs. See also [LDP-PAGING].

#### 5.2.2 HTTP GET

Per section 4.2.2 HTTP GET the HTTP GET method is required and additional
requirements can be found in section 5.2.1 General.

#### 5.2.3 HTTP POST

Per [RFC7231], this HTTP method is optional and this specification does not
require LDP servers to support it. When a LDP server supports this method,
this specification imposes the following new requirements for LDPCs.

Any server-imposed constraints on creation or update must be advertised to
clients.

##### 5.2.3.1 LDP clients _SHOULD_ create member resources by submitting a
representation as the entity body of the HTTP `POST` to a known LDPC. If the
resource was created successfully, LDP servers _MUST_ respond with status code
201 (Created) and the `Location` header set to the new resource's URL. Clients
shall not expect any representation in the response entity body on a 201
(Created) response.

##### 5.2.3.2  When a successful HTTP `POST` request to a LDPC results in the
creation of a LDPR, a containment triple _MUST_ be added to the state of the
LDPC whose subject is the LDPC URI, whose predicate is `ldp:contains` and
whose object is the URI for the newly created document (LDPR). Other triples
may be added as well. The newly created LDPR appears as a contained resource
of the LDPC until the newly created document is deleted or removed by other
methods.

##### 5.2.3.3 LDP servers _MAY_ accept an HTTP `POST` of non-RDF
representations (LDP-NRs) for creation of any kind of resource, for example
binary resources. See the Accept-Post section for details on how clients can
discover whether a LDPC supports this behavior.

##### 5.2.3.4 LDP servers that successfully create a resource from a RDF
representation in the request entity body _MUST_ honor the client's requested
interaction model(s). If any requested interaction model cannot be honored,
the server _MUST_ fail the request.

>   * If the request header specifies a LDPR interaction model, then the
server _MUST_ handle subsequent requests to the newly created resource's URI
as if it is a LDPR (even if the content contains an `rdf:type` triple
indicating a type of LDPC).

>   * If the request header specifies a LDPC interaction model, then the
server _MUST_ handle subsequent requests to the newly created resource's URI
as if it is a LDPC.

>   * This specification does not constrain the server's behavior in other
cases.

>

> Clients use the same syntax, that is `HTTP Link` headers, to specify the
desired interaction model when creating a resource as servers use to advertise
it on responses.

>

> Note: A consequence of this is that LDPCs can be used to create LDPCs, if
the server supports doing so.

##### 5.2.3.5 LDP servers that allow creation of LDP-RSs via POST _MUST_ allow
clients to create new members by enclosing a request entity body with a
`Content-Type` request header whose value is `text/turtle` [turtle].

##### 5.2.3.6 LDP servers _SHOULD_ use the `Content-Type` request header to
determine the request representation's format when the request has an entity
body.

##### 5.2.3.7 LDP servers creating a LDP-RS via POST _MUST_ interpret the null
relative URI for the subject of triples in the LDP-RS representation in the
request entity body as identifying the entity in the request body. Commonly,
that entity is the model for the "to be created" LDPR, so triples whose
subject is the null relative URI result in triples in the created resource
whose subject is the created resource.

##### 5.2.3.8 LDP servers _SHOULD_ assign the URI for the resource to be
created using server application specific rules in the absence of a client
hint.

##### 5.2.3.9 LDP servers _SHOULD_ allow clients to create new resources
without requiring detailed knowledge of application-specific constraints. This
is a consequence of the requirement to enable simple creation and modification
of LDPRs. LDP servers expose these application-specific constraints as
described in section 4.2.1 General.

##### 5.2.3.10 LDP servers _MAY_ allow clients to suggest the URI for a
resource created through `POST`, using the HTTP `Slug` header as defined in
[RFC5023]. LDP adds no new requirements to this usage, so its presence
functions as a client hint to the server providing a desired string to be
incorporated into the server's final choice of resource URI.

##### 5.2.3.11 LDP servers that allow member creation via `POST` _SHOULD NOT_
re-use URIs.

##### 5.2.3.12 Upon successful creation of an LDP-NR (HTTP status code of
201-Created and URI indicated by `Location` response header), LDP servers
_MAY_ create an associated LDP-RS to contain data about the newly created LDP-
NR. If a LDP server creates this associated LDP-RS, it _MUST_ indicate its
location in the response by adding a HTTP `Link` header with a context URI
identifying the newly created LDP-NR (instead of the effective request URI), a
link relation value of `describedby`, and a target URI identifying the
associated LDP-RS resource [RFC5988].

##### 5.2.3.13 LDP servers that support `POST` _MUST_ include an `Accept-Post`
response header on HTTP `OPTIONS` responses, listing `POST` request media
type(s) supported by the server. LDP only specifies the use of `POST` for the
purpose of creating new resources, but a server can accept `POST` requests
with other semantics. While "POST to create" is a common interaction pattern,
LDP clients are not guaranteed, even when making requests to a LDP server,
that every successful `POST` request will result in the creation of a new
resource; they must rely on out of band information for knowledge of which
`POST` requests, if any, will have the "create new resource" semantics. This
requirement on LDP servers is intentionally stronger than the one levied in
the header registration; it is unrealistic to expect all existing resources
that support `POST` to suddenly return a new header or for all new
specifications constraining `POST` to be aware of its existence and require
it, but it is a reasonable requirement for new specifications such as LDP.

Feature At Risk

The LDP Working Group proposes incorporation of the following clause requiring
JSON-LD support.

##### 5.2.3.14 LDP servers that allow creation of LDP-RSs via POST _MUST_
allow clients to create new members by enclosing a request entity body with a
`Content-Type` request header whose value is `application/ld+json` [JSON-LD].

#### 5.2.4 HTTP PUT

Per [RFC7231], this HTTP method is optional and this specification does not
require LDP servers to support it. When a LDP server supports this method,
this specification imposes the following new requirements for LDPCs.

Any server-imposed constraints on creation or update must be advertised to
clients.

##### 5.2.4.1 LDP servers _SHOULD NOT_ allow HTTP `PUT` to update a LDPC's
containment triples; if the server receives such a request, it _SHOULD_
respond with a 409 (Conflict) status code.

##### 5.2.4.2 LDP servers that allow LDPR creation via `PUT` _SHOULD NOT_ re-
use URIs.

#### 5.2.5 HTTP DELETE

Per [RFC7231], this HTTP method is optional and this specification does not
require LDP servers to support it. When a LDP server supports this method,
this specification imposes the following new requirements for LDPCs.

##### 5.2.5.1  When a contained LDPR is deleted, the LDPC server _MUST_ also
remove the corresponding containment triple, which has the effect of removing
the deleted LDPR from the containing LDPC.

> Non-normative note: The LDP server might perform additional actions, as
described in the normative references like [RFC7231]. For example, the server
could remove membership triples referring to the deleted LDPR, perform
additional cleanup tasks for resources it knows are no longer referenced or
have not been accessed for some period of time, and so on.

##### 5.2.5.2  When a contained LDPR is deleted, and the LDPC server created
an associated LDP-RS (see the LDPC POST section), the LDPC server _MUST_ also
delete the associated LDP-RS it created.

#### 5.2.6 HTTP HEAD

Note that certain LDP mechanisms rely on HTTP headers, and HTTP recommends
that `HEAD` responses include the same headers as `GET` responses. LDP servers
must also include HTTP headers on responses to `OPTIONS`, see section 4.2.8
HTTP OPTIONS. Thus, implementers supporting `HEAD` should also carefully read
the section 5.2.2 HTTP GET and section 5.2.8 HTTP OPTIONS.

#### 5.2.7 HTTP PATCH

Per [RFC5789], this HTTP method is optional and this specification does not
require LDP servers to support it. When a LDP server supports this method,
this specification imposes the following new requirements for LDPCs.

Any server-imposed constraints on LDPR creation or update must be advertised
to clients.

##### 5.2.7.1  LDP servers are _RECOMMENDED_ to support HTTP `PATCH` as the
preferred method for updating a LDPC's minimal-container triples.

#### 5.2.8 HTTP OPTIONS

This specification imposes the following new requirements on HTTP `OPTIONS`
for LDPCs. Note that support for this method is required for LDPCs, since it
is required for LDPRs and LDPCs adhere to LDP-RS requirements.

##### 5.2.8.1  When responding to requests whose `request-URI` is a LDP-NR
with an associated LDP-RS, a LDPC server _MUST_ provide the same HTTP `Link`
response header as is required in the create response.

  *[LDPRs]: Linked Data Platform Resources
  *[LDPCs]: Linked Data Platform Containers
  *[LDPR]: Linked Data Platform Resource
  *[LDPC]: Linked Data Platform Container
  *[LDP-RS]: Linked Data Platform RDF Source
  *[RDF]: Resource Description Framework
  *[LDP-NR]: Linked Data Platform Non-RDF Source
"""

from rdflib.namespace import Namespace, RDF
from rdflib import URIRef
from rdflib import Graph

from flask import render_template

from test.base import LDPTest, CONTINENTS, GN, PUT, AF, AS


from ldp import NS as LDP
from ldp.helpers import URL


BOB = URIRef('http://example.org/bob')

class LdpcGeneral(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    def test_5_2_1_1(self):
        """
        5.2.1.1 Each Linked Data Platform Container MUST also be 
        a conforming Linked Data Platform RDF Source. LDP clients MAY infer the following triple: one
        whose subject is the LDPC, 
        whose predicate is rdf:type, 
        and whose object is ldp:RDFSource, 
        but there is no requirement to materialize this triple in the LDPC representation.
        """
        pass

    def test_5_2_1_4(self):
        """
        5.2.1.4 LDP servers
        exposing LDPCs
        MUST advertise their LDP support by exposing a HTTP Link header
        with a target URI matching the type of container (see below) the
        server supports, and
        a link relation type of type (that is, rel='type')
        in all responses to requests made to the LDPC's HTTP Request-URI.
        LDP servers MAY provide additional HTTP Link: rel='type' headers.
        The notes on the corresponding LDPR constraint apply
        equally to LDPCs.

        Valid container type URIs for rel='type' defined by this document are:

        http://www.w3.org/ns/ldp#BasicContainer - for LDP Basic Containers
        http://www.w3.org/ns/ldp#DirectContainer - for LDP Direct Containers
        http://www.w3.org/ns/ldp#IndirectContainer - for LDP Indirect Containers
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'],
                       types=(LDP.BasicContainer, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)
        response = self.client.open('/x/AF', method='OPTIONS')
        self.assertIn('Container', response.headers['Link'])

    def test_5_2_1_5(self):
        """
        5.2.1.5 LDP servers
        SHOULD respect all of a client's LDP-defined hints, for example 
        which subsets of LDP-defined state
        the client is interested in processing,
        to influence the set of triples returned in representations of a LDPC, 
        particularly for large LDPCs.  See also [LDP-PAGING].
        """
        pass

POST = '''@prefix dcterms: <http://purl.org/dc/terms/>.
@prefix ldp: <http://www.w3.org/ns/ldp#>.
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#>.
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix cv: <http://purl.org/captsolo/resume-rdf/0.2/cv#> .

@base <{base}> .

<{name}> a foaf:Person;
  dcterms:title '{name}’s data storage on the Web' .
'''

POST_JSON = '''[
      {{
        "@id": "{base}{name}",
        "@type": [
          "http://xmlns.com/foaf/0.1/Person"
        ],
        "http://purl.org/dc/terms/title": [
          {{
            "@value": "bob\u2019s data storage on the Web"
          }}
        ]
      }}
    ]'''


class LdpcHttpPost(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    def test_5_2_3_1(self):
        """
        5.2.3.1 LDP clients SHOULD create member resources by submitting a representation as
the entity body of the HTTP POST to a known LDPC. If the resource was created successfully, LDP servers MUST
respond with status code 201 (Created) and the Location
header set to the new resource’s URL. Clients shall not expect any representation in the response
entity body on a 201 (Created) response.
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'],
                       types=(LDP.BasicContainer, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        @self.app.route('/person/<nick>')
        @self.app.bind('person', 'http://example.org/<nick>',
                       types=(LDP.RDFSource,))
        @self.app.bind('continent', AF,
                       types=(LDP.RDFSource,))
        def person(person, continent):
            return '%s' % (continent, person)

        response = self.client.open('/x/AF',
                                 method='POST',
                                 data=POST.format(base='http://example.org/',
                                                  name='bob'),
                                 headers={'Content-Type': 'text/turtle'})
        self.assertEqual(response.status_code, 201)

        self.assertEqual(response.headers['Location'], 'http://localhost/person/bob')

        response = self.client.open('/x/AF',
                                 method='POST',
                                 data=POST.format(base='http://example.org/',
                                                  name='bob'),
                                 headers={'Content-Type': 'text/turtle'})
        self.assertEqual(response.status_code, 409)
        response = self.client.open('/x/AF',
                                 method='POST',
                                 data=POST.format(base='http://example.orgXX/',
                                                  name='bob'),
                                 headers={'Content-Type': 'text/turtle'})
        self.assertEqual(response.status_code, 422)

    def test_5_2_3_2(self):
        """5.2.3.2 When a successful HTTP POST request to a LDPC results in the creation of a LDPR, a 
containment triple MUST be added to the state of the LDPC
whose subject is the LDPC URI, 
whose predicate is ldp:contains and whose object is the URI for the newly created document (LDPR).  Other triples may be added as well.
The newly created LDPR appears as a contained resource of the LDPC until the
newly created document is deleted or removed by other methods. 
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'],
                       types=(LDP.BasicContainer, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        @self.app.route('/person/<nick>')
        @self.app.bind('person', 'http://example.org/<nick>',
                       types=(LDP.RDFSource,))
        def person(person):
            return '%s' % person

        response = self.client.open('/x/AF',
                                    method='POST',
                                    data=POST.format(
                                        base='http://example.org/',
                                        name='bob'),
                                    headers={'Content-Type': 'text/turtle'})
        self.assertEqual(response.status_code, 201)
        g = Graph().parse(data=self.client.get('/x/AF',
                          headers={'Accept': 'text/turtle'}).data.decode(),
                          format='turtle')
        triples = list(g[:LDP.contains:BOB])
        self.assertTrue(triples)

#     def test_5_2_3_4(self):
#         """
#         5.2.3.4 LDP servers that successfully create a resource from a
#         RDF representation in the request entity body MUST honor the client's requested interaction model(s). 
#         If any requested interaction model cannot be honored, the server MUST fail the request.



# If the request header specifies a LDPR interaction model, then the server MUST handle subsequent 
# requests to the newly created resource's URI as if it is a LDPR
# (even if the content contains an rdf:type triple indicating a type of LDPC).
# If the request header specifies a LDPC interaction model, then the server MUST handle subsequent 
# requests to the newly created resource's URI as if it is a LDPC.

# This specification does not constrain the server's behavior in other cases.

# Clients use the same syntax, that is HTTP Link headers, to specify the desired interaction model
#         when creating a resource as servers use to advertise it on responses.

# Note: A consequence of this is that LDPCs can be used to create LDPCs, if the server supports doing so.
#         """
#         pass

#     def test_5_2_3_5(self):
#         """
#         5.2.3.5 LDP servers 
#     that allow creation of LDP-RSs via POST MUST 
#     allow clients to create new members by enclosing a request entity body with a 
# Content-Type request header whose value is text/turtle [turtle].
#         """
#         pass

#     def test_5_2_3_6(self):
#         """
#         5.2.3.6 LDP servers SHOULD use the Content-Type request header 
# to determine the request representation's format when the request has an entity body. 
#         """
#         pass

#     def test_5_2_3_7(self):
#         """
#         5.2.3.7 LDP servers  
# creating a LDP-RS via POST MUST 
# interpret the null relative
# URI for the subject of triples in the LDP-RS representation in the
# request entity body as identifying the entity in the request body.
# Commonly, that entity is the model for the "to be created" LDPR, so
# triples whose subject is the null relative URI result in
# triples in the created resource whose subject is the created
# resource.  
#         """
#         pass

#     def test_5_2_3_8(self):
#         """
#         5.2.3.8 LDP servers SHOULD assign the URI for the resource to be
# created using server application specific rules in the absence of a client hint.
#         """
#         pass

#     def test_5_2_3_9(self):
#         """
#         5.2.3.9 LDP servers SHOULD allow clients to create new resources without
# requiring detailed knowledge of application-specific constraints.
# This is a consequence of the requirement to enable simple creation and modification of LDPRs. LDP servers
# expose these application-specific constraints as described in section 4.2.1 General.
#         """
#         pass

    def test_5_2_3_12(self):
        """
        5.2.3.12 Upon successful creation of an  
        LDP-NR (HTTP status code of 
        201-Created and URI indicated by Location response header), LDP servers MAY create an associated 
        LDP-RS
        to contain data about the newly created LDP-NR.  
        If a LDP server creates this associated LDP-RS, it MUST indicate
        its location in the response by adding a HTTP Link header with 
        a context URI identifying the newly created LDP-NR (instead of the effective request URI),
        a link relation value of describedby,
        and a target URI identifying the associated LDP-RS resource [RFC5988].
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'],
                       types=(LDP.BasicContainer, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        @self.app.route('/person/<nick>')
        @self.app.bind('nick', 'http://example.org/<nick>',
                       types=(LDP.RDFSource,))
        def person(nick):
            return '%s' % nick

        response = self.client.open('/x/AF',
                                    method='POST',
                                    data=POST.format(
                                        base='http://example.org/',
                                        name='bob'),
                                    headers={'Content-Type': 'text/turtle'})
        response = self.client.get(URL(response.headers['Location']).path,
                                   headers={'Accept': 'text/turtle'})
        self.assertIn('data storage on the Web', response.data.decode())

    def test_5_2_3_13(self):
        """
        5.2.3.13 LDP servers that support POST MUST
        include an Accept-Post response header on HTTP OPTIONS
        responses, listing POST request media type(s) supported by the server.
        LDP only specifies the use of POST for the purpose of creating new resources, but a server
        can accept POST requests with other semantics.  
        While "POST to create" is a common interaction pattern, LDP clients are not guaranteed, even when 
        making requests to a LDP server, that every successful POST request will result in the 
        creation of a new resource; they must rely on out of band information for knowledge of which POST requests,
        if any, will have the "create new resource" semantics.
        This requirement on LDP servers is intentionally stronger than the one levied in the
        header registration; it is unrealistic to expect all existing resources
        that support POST to suddenly return a new header or for all new specifications constraining
        POST to be aware of its existence and require it, but it is a reasonable requirement for new
        specifications such as LDP.
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'],
                       types=(LDP.BasicContainer, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        @self.app.route('/person/<nick>')
        @self.app.bind('nick', 'http://example.org/<nick>',
                       types=(LDP.RDFSource,))
        def person(nick):
            return '%s' % nick


        response = self.client.open('/x/AF', method='OPTIONS')
        self.assertIn('Accept-Post', response.headers)

    def test_5_2_3_14(self):
        """
        5.2.3.14 LDP servers 
        that allow creation of LDP-RSs via POST MUST 
        allow clients to create new members by enclosing a request entity body with a 
        Content-Type request header whose value is application/ld+json [JSON-LD].
        """

        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'],
                       types=(LDP.BasicContainer, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        @self.app.route('/person/<nick>')
        @self.app.bind('person', 'http://example.org/<nick>',
                       types=(LDP.RDFSource,))
        def person(person):
            return '%s' % person

        response = self.client.open('/x/AF',
                                    method='POST',
                                    data=POST_JSON.format(
                                        base='http://example.org/',
                                        name='bob'),
                                    headers={'Content-Type': 'application/ld+json'})
        self.assertEqual(response.status_code, 201)
        g = Graph().parse(data=self.client.get('/x/AF',
                          headers={'Accept': 'text/turtle'}).data.decode(),
                          format='turtle')
        triples = list(g[:LDP.contains:BOB])
        self.assertTrue(triples)

PUT_CONFLICT = '''@prefix dc: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix gn: <http://www.geonames.org/ontology#> .

<http://www.telegraphis.net/data/continents/{0}#{0}> a foaf:PersonalProfileDocument;
    foaf:primaryTopic <#me> ;
    gn:population "922011001" ;
    dc:title "Alice’s FOAF file" .
'''
PUT_NON_CONFLICT = '''@prefix dc: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix gn: <http://www.geonames.org/ontology#> .

<http://www.telegraphis.net/data/continents/{0}#{0}> a foaf:PersonalProfileDocument;
    foaf:primaryTopic <#me> ;
    gn:population "922011001" ;
    <http://www.w3.org/ns/ldp#contains> <http://example.org/bob> ;
    dc:title "Alice’s FOAF file" .
'''

class LdpcHttpPut(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    def test_5_2_4_1(self):
        """
        5.2.4.1 LDP servers SHOULD NOT allow HTTP PUT to update a LDPC’s containment triples; 
if the server receives such a request, it SHOULD respond with a 409
(Conflict) status code.
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'],
                       types=(LDP.BasicContainer, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        @self.app.route('/person/<nick>')
        @self.app.bind('person', 'http://example.org/<nick>',
                       types=(LDP.RDFSource,))
        def person(person):
            return '%s' % person

        response = self.client.open('/x/AF',
                                 method='POST',
                                 data=POST_JSON.format(base='http://example.org/',
                                                       name='bob'),
                                 headers={'Content-Type': 'application/ld+json'})        

        response = self.client.open('/x/AF',
                                 method='PUT',
                                 data=PUT_CONFLICT.format('AF'),
                                 headers={'Content-Type': 'text/turtle'})

        self.assertEqual(response.status_code, 409)
        response = self.client.open('/x/AF',
                                 method='PUT',
                                 data=PUT_NON_CONFLICT.format('AF'),
                                 headers={'Content-Type': 'text/turtle'})

        self.assertEqual(response.status_code, 204)


class LdpcHttpDelete(LDPTest):

    def test_5_2_5_1(self):
        """
        5.2.5.1 
        When a contained LDPR is deleted, the LDPC server MUST also remove 
        the corresponding containment triple, which has the effect of removing the deleted LDPR from the containing LDPC.


        Non-normative note: The LDP server might perform additional actions, 
        as described in the normative references like [RFC7231]. 
        For example, the server could remove membership triples referring to the deleted LDPR, 
        perform additional cleanup tasks for resources it knows are no longer referenced or have not
        been accessed for some period of time, and so on.
        """
        pass

    def test_5_2_5_2(self):
        """
        5.2.5.2 
        When a contained LDPR is deleted, and the LDPC server 
        created an associated LDP-RS (see the LDPC POST section), the LDPC server MUST also delete the associated LDP-RS it created.
        """
        pass


class LdpcHttpOptions(LDPTest):

    def test_5_2_8_1(self):
        """
        5.2.8.1 
        When responding to requests whose request-URI is a 
        LDP-NR with an associated LDP-RS, 
        a LDPC server MUST provide the same HTTP Link
        response header as is required in the create response.
        """
        pass