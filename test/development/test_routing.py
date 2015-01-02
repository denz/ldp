from base64 import b64encode

from werkzeug.http import parse_set_header

from ldp import NS as LDP
from test.base import LDPTest, CONTINENTS, GN, PUT


class TestRouting(LDPTest):
    DATASET_DESCRIPTORS = {'continents': {'source': 'test/continents.rdf',
                           'publicID': CONTINENTS}}

    def test_without_binding(self):
        @self.app.route('/')
        def view():
            return 'DONE'

        @self.app.route('/<x>')
        def viewx(x):
            return 'DONE %s' % x

        self.assertEqual(self.client.get('/').status_code, 200)

        self.assertEqual(self.client.get('/222').status_code, 200)

    def test_singletone_binding(self):
        @self.app.route('/')
        @self.app.bind('root', CONTINENTS['AF#AF'])
        def view0(root):
            return 'DONE %r' % root

        @self.app.route('/x')
        @self.app.bind('root', CONTINENTS['AF#AX'])
        def view1(root):
            return 'DONE %r' % root

        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/x').status_code, 404)

    def test_simple_binding(self):
        @self.app.route('/x/<c>')
        @self.app.bind('c', CONTINENTS['<c>#<c>'])
        def population(c):
            return c.value(GN.population)

        response = self.client.get('/x/AF')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'922011000')
        self.assertEqual(self.client.get('/x/XX').status_code, 404)

    def test_multi_binding(self):
        with self.assertRaises(AssertionError):
            @self.app.route('/y/<c>')
            @self.app.bind('p', CONTINENTS['<p>#<p>'])
            @self.app.bind('c', CONTINENTS['<c>#<c>'])
            def view0(p, x=1):
                return 'DONE %r' % p

        with self.assertRaises(AssertionError):
            @self.app.route('/y/<p>')
            @self.app.bind('v', CONTINENTS['<v>#<v>'])
            @self.app.bind('p', CONTINENTS['<p>#<p>'])
            def view1(p, v):
                return '%s %s' % (p, v)

        @self.app.route('/y/<p>/<v>')
        @self.app.bind('v', CONTINENTS['<v>#<v>'])
        @self.app.bind('p', CONTINENTS['<p>#<p>'])
        def view2(p, v, *args):
            return 'DONE %r' % p

        @self.app.route('/y/<p>/<v>')
        @self.app.bind('v', CONTINENTS['<v>#<v>'])
        @self.app.bind('p', CONTINENTS['<p>#<p>'])
        def view3(p, *args, **kwargs):
            return 'DONE %r' % p

        @self.app.route('/y/<p>/<v>')
        @self.app.bind('v', CONTINENTS['<v>#<v>'])
        @self.app.bind('p', CONTINENTS['<p>#<p>'])
        def view4(p, **kwargs):
            return '%s %s' % (p, kwargs)

    def test_matching_and_converting(self):
        @self.app.route('/y/<b64:c>')
        @self.app.bind('c', '<c>')
        def view0(c):
            return c.identifier

        url = '/y/%s' % b64encode(bytes(CONTINENTS['AF#AF'],
              'ascii')).decode()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, bytes(CONTINENTS['AF#AF'], 'ascii'))

    def test_typed_binding(self):
        @self.app.route('/x/<continent>')
        @self.app.bind('continent',
                       CONTINENTS['<continent>#<continent>'],
                       types=(LDP.RDFSource,))
        def c0(continent):
            return '%s' % (continent)

        @self.app.route('/y/<continent>')
        @self.app.bind('continent',
                       CONTINENTS['<continent>#<continent>'],
                       types=(LDP.Resource,))
        def c1(continent):
            return '%s' % (continent)

        @self.app.route('/z/<continent>')
        def c2(continent):
            return '%s' % (continent)

        headers = parse_set_header(
            self.client.open('/x/AF',
                             method='PUT',
                             data=PUT.format('AF')).headers['Link'])
        self.assertIn('RDFSource', ''.join(headers))
        self.assertIn('Resource', ''.join(headers))

        headers = parse_set_header(
            self.client.open('/y/AF',
                             method='PUT',
                             data=PUT.format('AF')).headers['Link'])
        self.assertIn('Resource', ''.join(headers))
        self.assertNotIn('RDFSource', ''.join(headers))

        headers = parse_set_header(
            self.client.get('/x/AF').headers['Link'])
        self.assertIn('Resource', ''.join(headers))
        self.assertIn('NonRDFSource', ''.join(headers))

        headers = parse_set_header(
            self.client.get('/y/AF').headers['Link'])
        self.assertIn('Resource', ''.join(headers))
        self.assertIn('NonRDFSource', ''.join(headers))

        headers = parse_set_header(
            self.client.get('/y/AF').headers['Link'])

        self.assertFalse(self.client.get('/z/AF').headers['Link'])

