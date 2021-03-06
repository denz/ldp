"""
# 4.2 Resource

# 4.2.1 General

# 4.2.1.1 LDP servers _MUST_ at least be HTTP/1.1 conformant servers
[RFC7230].

# 4.2.1.2 LDP servers _MAY_ host a mixture of LDP-RSs and LDP-NRs. For
example, it is common for LDP servers to need to host binary or text resources
that do not have useful RDF representations.

# 4.2.1.3 LDP server responses _MUST_ use entity tags (either weak or
strong ones) as response `ETag` header values, for responses that contain
resource representations or successful responses to HTTP `HEAD` requests.

# 4.2.1.4 LDP servers exposing LDPRs _MUST_ advertise their LDP support by
exposing a HTTP `Link` header with a target URI of
`http://www.w3.org/ns/ldp#Resource`, and a link relation type of `type` (that
is, `rel='type'`) in all responses to requests made to an LDPR's HTTP
`Request-URI` [RFC5988].

> Note: The HTTP `Link` header is the method by which servers assert their
support for the LDP specification on a specific resource in a way that clients
can inspect dynamically at run-time. This is **not** equivalent to the
presence of a (subject-URI, `rdf:type`, `ldp:Resource`) triple in an LDP-RS.
The presence of the header asserts that the server complies with the LDP
specification's constraints on HTTP interactions with LDPRs, that is it
asserts that the resource has Etags, supports OPTIONS, and so on, which is not
true of all Web resources.

>

> Note: A LDP server can host a mixture of LDP-RSs and LDP-NRs, and therefore
there is no implication that LDP support advertised on one HTTP `Request-URI`
means that other resources on the same server are also LDPRs. Each HTTP
`Request-URI` needs to be individually inspected, in the absence of outside
information.

# 4.2.1.5 LDP servers _MUST_ assign the default base-URI for [RFC3987]
relative-URI resolution to be the HTTP `Request-URI` when the resource already
exists, and to the URI of the created resource when the request results in the
creation of a new resource.

# 4.2.1.6 LDP servers _MUST_ publish any constraints on LDP clients'
ability to create or update LDPRs, by adding a Link header with an appropriate
context URI, a link relation of `http://www.w3.org/ns/ldp#constrainedBy`, and
a target URI identifying a set of constraints [RFC5988], to all responses to
requests that fail due to violation of those constraints. For example, a
server that refuses resource creation requests via HTTP PUT, POST, or PATCH
would return this `Link` header on its 4xx responses to such requests. The
same `Link` header _MAY_ be provided on other responses. LDP neither defines
nor constrains the representation of the link's target resource. Natural
language constraint documents are therefore permitted, although machine-
readable ones facilitate better client interactions. The appropriate context
URI can vary based on the request's semantics and method; unless the response
is otherwise constrained, the default (the effective request URI) _SHOULD_ be
used.

# 4.2.2 HTTP GET

# 4.2.2.1 LDP servers _MUST_ support the HTTP `GET` Method for LDPRs.

# 4.2.2.2 LDP servers _MUST_ support the HTTP response headers defined in
section 4.2.8 HTTP OPTIONS.

# 4.2.3 HTTP POST

Per [RFC7231], this HTTP method is optional and this specification does not
require LDP servers to support it. When a LDP server supports this method,
this specification imposes no new requirements for LDPRs.

Clients can create LDPRs via `POST` (section 5.2.3 HTTP POST) to a LDPC, via
`PUT` (section 4.2.4 HTTP PUT), or any other methods allowed for HTTP
resources. Any server-imposed constraints on LDPR creation or update must be
advertised to clients.

# 4.2.4 HTTP PUT

Per [RFC7231], this HTTP method is optional and this specification does not
require LDP servers to support it. When a LDP server supports this method,
this specification imposes the following new requirements for LDPRs.

Any server-imposed constraints on LDPR creation or update must be advertised
to clients.

# 4.2.4.1 If a HTTP `PUT` is accepted on an existing resource, LDP servers
_MUST_ replace the entire persistent state of the identified resource with the
entity representation in the body of the request. LDP servers _MAY_ ignore
server-managed properties such as `dcterms:modified` and `dcterms:creator` if
they are not under client control. Any LDP servers that wish to support a more
sophisticated merge of data provided by the client with existing state stored
on the server for a resource _MUST_ use HTTP `PATCH`, not HTTP `PUT`.

# 4.2.4.2 LDP servers _SHOULD_ allow clients to update resources without
requiring detailed knowledge of server-specific constraints. This is a
consequence of the requirement to enable simple creation and modification of
LDPRs.

# 4.2.4.3  If an otherwise valid HTTP `PUT` request is received that
attempts to change properties the server does not allow clients to modify, LDP
servers _MUST_ fail the request by responding with a 4xx range status code
(typically 409 Conflict). LDP servers _SHOULD_ provide a corresponding
response body containing information about which properties could not be
persisted. The format of the 4xx response body is not constrained by LDP.

> Non-normative note: Clients might provide properties equivalent to those
already in the resource's state, e.g. as part of a GET/update
representation/PUT sequence, and those PUT requests are intended to work as
long as the server-managed properties are identical on the GET response and
the subsequent PUT request. This is in contrast to other cases like write-once
properties that the server does not allow clients to modify once set; write-
once properties are under client control, they are not server-managed.

# 4.2.4.4  If an otherwise valid HTTP `PUT` request is received that
contains properties the server chooses not to persist, e.g. unknown content,
LDP servers _MUST_ respond with an appropriate 4xx range status code
[RFC7231]. LDP servers _SHOULD_ provide a corresponding response body
containing information about which properties could not be persisted. The
format of the 4xx response body is not constrained by LDP. LDP servers expose
these application-specific constraints as described in section 4.2.1 General.

# 4.2.4.5 LDP clients _SHOULD_ use the HTTP `If-Match` header and HTTP
`ETags` to ensure it isn't modifying a resource that has changed since the
client last retrieved its representation. LDP servers _SHOULD_ require the
HTTP `If-Match` header and HTTP `ETags` to detect collisions. LDP servers
_MUST_ respond with status code 412 (Condition Failed) if `ETag`s fail to
match when there are no other errors with the request [RFC7232]. LDP servers
that require conditional requests _MUST_ respond with status code 428
(Precondition Required) when the absence of a precondition is the only reason
for rejecting the request [RFC6585].

# 4.2.4.6 LDP servers _MAY_ choose to allow the creation of new resources
using HTTP `PUT`.

# 4.2.5 HTTP DELETE

Per [RFC7231], this HTTP method is optional and this specification does not
require LDP servers to support it. When a LDP server supports this method,
this specification imposes no new blanket requirements for LDPRs.

Additional requirements on HTTP `DELETE` for LDPRs within containers can be
found in section 5.2.5 HTTP DELETE.

# 4.2.6 HTTP HEAD

Note that certain LDP mechanisms rely on HTTP headers, and HTTP generally
requires that `HEAD` responses include the same headers as `GET` responses.
Thus, implementers should also carefully read sections 4.2.2 HTTP GET and
4.2.8 HTTP OPTIONS.

# 4.2.6.1 LDP servers _MUST_ support the HTTP `HEAD` method.

# 4.2.7 HTTP PATCH

Per [RFC5789], this HTTP method is optional and this specification does not
require LDP servers to support it. When a LDP server supports this method,
this specification imposes the following new requirements for LDPRs.

Any server-imposed constraints on LDPR creation or update must be advertised
to clients.

# 4.2.7.1 LDP servers that support `PATCH` _MUST_ include an `Accept-
Patch` HTTP response header [RFC5789] on HTTP `OPTIONS` requests, listing
patch document media type(s) supported by the server.

# 4.2.8 HTTP OPTIONS

This specification imposes the following new requirements on HTTP `OPTIONS`
for LDPRs beyond those in [RFC7231]. Other sections of this specification, for
example PATCH, Accept-Post, add other requirements on `OPTIONS` responses.

# 4.2.8.1 LDP servers _MUST_ support the HTTP `OPTIONS` method.

# 4.2.8.2 LDP servers _MUST_ indicate their support for HTTP Methods by
responding to a HTTP `OPTIONS` request on the LDPR's URL with the HTTP Method
tokens in the HTTP response header `Allow`.

  *[LDPRs]: Linked Data Platform Resources
  *[LDP-RS]: Linked Data Platform RDF Source
  *[RDF]: Resource Description Framework
  *[LDPR]: Linked Data Platform Resource
  *[LDPC]: Linked Data Platform Container
"""
from pprint import pprint

from rdflib.namespace import Namespace, RDF
from rdflib import URIRef

from flask import render_template

from test.base import LDPTest, CONTINENTS, GN, PUT, AF, AS


from ldp import NS as LDP


class LdprGeneral(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    # def test_4_2_1_1(self):
    #     """
    #     4.2.1.1 LDP servers MUST at least be HTTP/1.1 conformant servers [RFC7230].
        
    #     """
    #     pass

    def test_4_2_1_3(self):
        """
        4.2.1.3 LDP server responses MUST use entity tags (either
        weak or strong ones) as response ETag header values, for
        responses that contain resource representations or
        successful responses to HTTP HEAD requests.
        """
        
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'])
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        response = self.client.get('/x/AF')
        self.assertTrue(response.headers['ETag'])

    def test_4_2_1_4(self):
        """
        4.2.1.4 LDP servers exposing LDPRs
        MUST advertise their LDP support by exposing a HTTP Link header
        with a target URI of http://www.w3.org/ns/ldp#Resource, and
        a link relation type of type (that is, rel='type')
        in all responses to requests made
        to an LDPR's HTTP Request-URI [RFC5988].
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'])
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        self.assertIn(LDP.Resource,
                      self.client.get('/x/AF').headers['Link'])

        # self.assertIn(LDP.Resource,
        #               self.client.open('/x/AF', method='PUT').headers['Link'])

        self.assertIn(LDP.Resource,
                      self.client.open('/x/AF', method='OPTIONS').headers['Link'])

        self.assertIn(LDP.Resource,
                      self.client.open('/x/AF', method='HEAD').headers['Link'])

#     def test_4_2_1_5(self):
#         """
#         4.2.1.5 LDP servers MUST assign the default
# base-URI for [RFC3987] relative-URI resolution to be the HTTP
# Request-URI when the resource already exists, and to the URI of the created resource when the request results
# in the creation of a new resource.
#         """
#         pass

#     def test_4_2_1_6(self):
#         """
#         4.2.1.6 LDP servers MUST
# publish any constraints on LDP clients’ ability to
# create or update LDPRs, by adding a Link header with
# an appropriate context URI,
# a link relation of http://www.w3.org/ns/ldp#constrainedBy,
# and a target URI identifying a set of constraints
# [RFC5988], to all responses to requests that fail due to violation of
# those constraints.  For example, a server that refuses resource creation
# requests via HTTP PUT, POST, or PATCH would return this Link header on its
# 4xx responses to such requests.
# The same Link header MAY be provided on other responses.  LDP neither
# defines nor constrains the representation of the link's target resource.  Natural language
# constraint documents are therefore permitted,
# although machine-readable ones facilitate better client interactions.
# The appropriate context URI can vary based on the request's semantics and method;
# unless the response is otherwise
# constrained, the default (the effective request URI) SHOULD be used.
#         """
#         pass


class LdprHttpGet(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    def test_4_2_2_1(self):
        """
        4.2.2.1 LDP servers MUST support the HTTP GET Method for LDPRs.
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'])
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        response = self.client.get('/x/AF')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/y/AF')
        self.assertEqual(response.status_code, 404)

    def test_4_2_2_2(self):
        """
        4.2.2.2 LDP servers MUST support the HTTP response headers defined in
        section 4.2.8 HTTP OPTIONS.
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'], types=(LDP.Resource,))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        response = self.client.open('/x/AF', method='OPTIONS')
        allow = set((m.strip() for m in response.headers['Allow'].split(',')))
        self.assertEqual(allow,
                         set(['OPTIONS', 'GET', 'HEAD', 'PUT']))


class LdprHttpPut(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}
    def test_4_2_4_1(self):
        """
        4.2.4.1 If a HTTP PUT is accepted on an existing resource,
        LDP servers MUST
        replace the entire persistent state of the identified resource with
        the entity representation in the body of the request.
        LDP servers MAY ignore server-managed properties such as dcterms:modified
        and dcterms:creator if they are not under
        client control. Any LDP servers that wish
        to support a more sophisticated merge of data provided by the client
        with existing state stored on the server for a resource MUST use HTTP
        PATCH, not HTTP PUT.
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'], types=(LDP.RDFSource,))
        def population(c):
            return render_template('test.html', c=c, GN=GN)        

        response = self.client.open('/x/AN',
                                    method='PUT',
                                    data=PUT.format('AN'),
                                    headers={'Content-Type': 'text/turtle'})
        self.assertIn('foaf:primaryTopic',
                      self.client.open('/x/AN',
                                       method='GET',
                                       headers={'Accept':'text/turtle'})
                      .data.decode())
    # def test_4_2_4_2(self):
    #     """
    #     4.2.4.2 LDP servers SHOULD allow clients to update resources without
    #     requiring detailed knowledge of server-specific constraints.
    #     This is a consequence of the requirement to enable simple creation and modification of LDPRs.
    #     """
    #     pass

    # def test_4_2_4_3(self):
    #     """
    #     4.2.4.3
    #     If an otherwise valid HTTP PUT request is received
    #     that attempts to change properties the server does not allow clients to modify,
    #     LDP servers MUST
    #     fail the request by responding with a 4xx range status code (typically
    #     409 Conflict).
    #     LDP servers SHOULD provide a corresponding response body containing
    #     information about which properties could not be
    #     persisted.
    #     The format of the 4xx response body is not constrained by LDP.
    #     """
    #     # response = self.app.open('/resource/AS',
    #     #                  method='PUT',
    #     #                  data=CONFLICTING_PUT.format('AS'),
    #     #                  headers={'Content-Type':'text/turtle'})

    #     # self.assertEqual(response.status_code, 409)

#     def test_4_2_4_4(self):
#         """
#         4.2.4.4
# If an otherwise valid HTTP PUT request is received that contains properties the server
# chooses not to persist, e.g. unknown content,
# LDP servers MUST respond with an appropriate 4xx range status code
# [RFC7231].
# LDP servers SHOULD provide a corresponding response body containing
# information about which properties could not be
# persisted.
# The format of the 4xx response body is not constrained by LDP. LDP servers
# expose these application-specific constraints as described in section 4.2.1 General.
#         """
#         pass

    def test_4_2_4_5(self):
        """
        4.2.4.5 LDP clients SHOULD use the HTTP If-Match
        header and HTTP ETags to ensure it isn’t
        modifying a resource that has changed since the client last retrieved
        its representation. LDP servers SHOULD require the HTTP If-Match header and HTTP ETags
        to detect collisions. LDP servers MUST respond with status code 412
        (Condition Failed) if ETags fail to match when there are no other
        errors with the request [RFC7232].  LDP servers that require conditional requests MUST respond with status code 428
        (Precondition Required) when the absence of a precondition is the only reason for rejecting the request [RFC6585].
        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'], types=(LDP.RDFSource, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        @self.app.route('/y/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'], types=(LDP.RDFSource, ))
        @self.app.bind('af', AF, types=(LDP.RDFSource, ))
        @self.app.bind('asia', AS, types=(LDP.RDFSource, ))
        def aggregate_continents(c, af, asia):
            return render_template('test.html', c=c, GN=GN)          

        response = self.client.open('/x/OC', method='HEAD')

        etag = response.headers['ETag']
        response = self.client.open('/x/OC',
                                 method='PUT',
                                 data=PUT.format('OC'),
                                 headers={'Content-Type': 'text/turtle',
                                          'If-Match': etag,
                                          })
        self.assertEqual(response.status_code, 204)
        response = self.client.get('/x/OC', headers={'Accept':'text/turtle'})
        self.assertIn('foaf:primaryTopic',
                      response.data.decode())
        response = self.client.open('/x/OC',
                                 method='PUT',
                                 data=PUT.format('OC'),
                                 headers={'Content-Type': 'text/turtle',
                                          'If-Match': etag + 'x'})

        self.assertEqual(response.status_code, 412)

        response = self.client.open('/y/OC', method='HEAD')

        etag = response.headers['ETag']
        response = self.client.open('/y/OC',
                                 method='PUT',
                                 data=PUT.format('OC'),
                                 headers={'Content-Type': 'text/turtle',
                                          'If-Match': etag,
                                          })
        self.assertEqual(response.status_code, 204)
        response = self.client.get('/y/OC', headers={'Accept': 'text/turtle'})
        self.assertIn('foaf:primaryTopic',
                      response.data.decode())
        response = self.client.open('/y/OC',
                                    method='PUT',
                                    data=PUT.format('OC'),
                                    headers={'Content-Type': 'text/turtle',
                                             'If-Match': etag + 'x'})

        self.assertEqual(response.status_code, 412)


class LdprHttpHead(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    def test_4_2_6_1(self):
        """
        4.2.6.1 LDP servers MUST support the HTTP HEAD method.

        """
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'], types=(LDP.RDFSource, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        response = self.client.open('/x/AF', method='HEAD')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'')
        self.assertIn('Etag', response.headers)
        self.assertIn('Link', response.headers)


class LdprHttpPatch(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    def test_4_2_7_1(self):
        """
        4.2.7.1 LDP servers that support PATCH MUST
        include an Accept-Patch HTTP response header [RFC5789] on HTTP OPTIONS
        requests, listing patch document media type(s) supported by the server.
        """
        @self.app.route('/x/<c>', methods=('GET', 'PATCH'))
        @self.app.bind('c', CONTINENTS['<c>#<c>'], types=(LDP.RDFSource, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        @self.app.route('/y/<c>', methods=('GET', ))
        @self.app.bind('c', CONTINENTS['<c>#<c>'], types=(LDP.RDFSource, ))
        def population_x(c):
            return render_template('test.html', c=c, GN=GN)

        response = self.client.open('/x/AF', method='OPTIONS')
        self.assertIn('Accept-Patch', response.headers)
        self.assertIn("application/ld+json", response.headers['Accept-Patch'])
        self.assertIn("text/turtle", response.headers['Accept-Patch'])

        response = self.client.open('/y/AF', method='OPTIONS')
        self.assertNotIn('Accept-Patch', response.headers)


class LdprHttpOptions(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    def test_4_2_8_1(self):
        """
        4.2.8.1 LDP servers MUST support the HTTP OPTIONS method.
        """
        @self.app.route('/x/<c>', methods=('GET', 'PATCH'))
        @self.app.bind('c', CONTINENTS['<c>#<c>'], types=(LDP.RDFSource, ))
        def population(c):
            return render_template('test.html', c=c, GN=GN)

        response = self.client.open('/x/AF', method='OPTIONS')
        self.assertEqual(response.status_code, 200)

#     def test_4_2_8_2(self):
#         """
#         4.2.8.2 LDP servers MUST indicate their support for HTTP Methods by
# responding to a HTTP OPTIONS request on the LDPR’s URL with the HTTP
# Method tokens in the HTTP response header Allow.
#         """
#         pass
