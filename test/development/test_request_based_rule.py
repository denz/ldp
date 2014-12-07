import json

from unittest import TestCase
from flask import Flask
from ldp.resource import Resource
from ldp.rule import match_headers
from ldp import LDPApp

class HeadersBasedRuleTest(TestCase):
    def setUp(self):
        self.app = LDPApp(__name__)
        self.app.debug = True
        self.c = self.app.test_client()

class TestHeaderMatch(HeadersBasedRuleTest):

    def test_simple_matching(self):
        @self.app.route(match_headers('/', Accept='application/json'))
        def json():
            return 'JSON'

        @self.app.route('/')
        def view():
            return 'DEFAULT'
        response = self.c.get('/', headers={})
        self.assertEqual(response.data, b'DEFAULT')

        response = self.c.get('/', headers={'Accept':'application/json'})
        self.assertEqual(response.data, b'JSON')



    def test_parameter_matching(self):
        @self.app.route(match_headers('/', Accept='application/json', Test='x<int:i>'))
        def json_p(**kwargs):
            return 'JSON%s'%kwargs['i']

        @self.app.route(match_headers('/', Accept='application/json'))
        def json():
            return 'JSON'

        @self.app.route('/')
        def view():
            return 'DEFAULT'

        response = self.c.get('/', headers={})
        self.assertEqual(response.data, b'DEFAULT')

        response = self.c.get('/', headers={'Accept':'application/json'})
        self.assertEqual(response.data, b'JSON')

        response = self.c.get('/', headers={'Accept':'application/json', 'Test':'x20'})
        self.assertEqual(response.data, b'JSON20')

class TestArgumentsCombinations(HeadersBasedRuleTest):     

    def test_0(self):
        @self.app.route('/')
        def view():
            return json.dumps({})

        response = self.c.get('/')
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {})

        response = self.c.get('/ttt')
        self.assertTrue(response.status_code, 404)

    def test_1(self):
        @self.app.route(match_headers('/',  **{'Accept': 'text/turtle'}))
        def view():
            return json.dumps({})

        response = self.c.get('/', headers={'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {})

        response = self.c.get('/', headers={})
        self.assertTrue(response.status_code, 404)

    def test_2(self):
        @self.app.route(match_headers('/',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=xx'})
        self.assertTrue(response.status_code, 404)

    def test_3(self):
        @self.app.route(match_headers('/',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/', headers={'Cache-Control':'public,\tmax-age=30'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/', headers={'Cache-Control': 'public,  max-age=30'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=xx'})
        self.assertTrue(response.status_code, 404)

    def test_4(self):
        @self.app.route(match_headers('/',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>',
                                         'Accept': 'text/*'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=xx',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30',
                                            'Accept': 'application/turtle'})
        self.assertTrue(response.status_code, 404)

    def test_5(self):
        @self.app.route(match_headers('/',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>',
                                         'Accept': 'text/*'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=30'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=xx',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=30',
                                            'Accept': 'application/turtle'})
        self.assertTrue(response.status_code, 404)

    def test_6(self):
        @self.app.route(match_headers('/',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>',
                                         'Accept': 'text/turtle'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public,  max-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)

    def test_7(self):
        @self.app.route(match_headers('/',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>',
                                         'Accept': 'text/turtle'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=30'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=xx',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=30',
                                            'Accept': 'application/turtle'})
        self.assertTrue(response.status_code, 404)


    def test_8(self):
        @self.app.route(match_headers('/',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>',
                                         'Accept': 'text/<mime>'}))
        def view(max_age, mime):
            return json.dumps({'max_age':max_age,'mime':mime})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30, 'mime':'turtle'})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=xx', 'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30', 'Accept': 'application/turtle'})
        self.assertTrue(response.status_code, 404)


    def test_9(self):
        @self.app.route(match_headers('/',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>',
                                         'Accept': 'text/<mime>'}))
        def view(max_age, mime):
            return json.dumps({'max_age':max_age,'mime':mime})

        response = self.c.get('/', headers={'Cache-Control': 'public,\tmax-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30, 'mime':'turtle'})

        response = self.c.get('/', headers={'Cache-Control': 'public, max-age=30',
                                            'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30, 'mime':'turtle'})


    def test_10(self):
        @self.app.route('/test/')
        def view():
            return json.dumps({})

        response = self.c.get('/test/', headers={'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {})


    def test_11(self):
        @self.app.route(match_headers('/test/',
                                      **{'Accept': 'text/turtle'}))
        def view():
            return json.dumps({})

        response = self.c.get('/test/', headers={'Accept': 'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {})

        response = self.c.get('/test/', headers={'Accept': 'application/turtle'})
        self.assertTrue(response.status_code, 404)

    def test_12(self):
        @self.app.route(match_headers('/test/',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/testz/', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 404)

    def test_13(self):
        @self.app.route(match_headers('/test/',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/test/', headers={'Cache-Control': 'public,\tmax-age=30'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/testz/', headers={'Cache-Control': 'public, \tmax-age=30'})
        self.assertTrue(response.status_code, 404)

    def test_14(self):
        @self.app.route(match_headers('/test/',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>',
                                         'Accept': 'text/*'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=30',
                                                 'Accept':'text/anything'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=30',
                                                 'Accept':'XXX/anything'})
        self.assertTrue(response.status_code, 404)

    def test_15(self):
        @self.app.route(match_headers('/test/',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>',
                                         'Accept': 'text/*'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/test/', headers={'Cache-Control': 'public,\tmax-age=30',
                                                 'Accept':'text/anything'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=30',
                                                 'Accept':'text/anything'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, \tmax-age=30',
                                                 'Accept':'text/anything'})
        self.assertTrue(response.status_code, 404)

    def test_16(self):
        @self.app.route(match_headers('/test/',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>',
                                         'Accept': 'text/turtle'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=30',
                                                 'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=xx',
                                                 'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 404)

    def test_17(self):
        @self.app.route(match_headers('/test/',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>',
                                         'Accept': 'text/turtle'}))
        def view(max_age):
            return json.dumps({'max_age':max_age})

        response = self.c.get('/test/', headers={'Cache-Control': 'public,\tmax-age=30',
                                                 'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=30',
                                                 'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, \testmax-age=30',
                                                 'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 404)

    def test_18(self):
        @self.app.route(match_headers('/test/',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>',
                                         'Accept': 'text/<mime>'}))
        def view(max_age, mime):
            return json.dumps({'max_age':max_age,'mime':mime})

        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=30',
                                                 'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30, 'mime':'turtle'})

    def test_19(self):
        @self.app.route(match_headers('/test/',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>',
                                         'Accept': 'text/<mime>'}))
        def view(max_age, mime):
            return json.dumps({'max_age':max_age,'mime':mime})

        response = self.c.get('/test/', headers={'Cache-Control': 'public,\tmax-age=30',
                                                 'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30, 'mime':'turtle'})


        response = self.c.get('/test/', headers={'Cache-Control': 'public, max-age=30',
                                                 'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'max_age':30, 'mime':'turtle'})

    def test_20(self):
        @self.app.route('/<int:x>')
        def view(x,):
            return json.dumps({'x':x})

        response = self.c.get('/23')
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23})

        response = self.c.get('/xx')
        self.assertTrue(response.status_code, 404)

    def test_21(self):
        @self.app.route(match_headers('/<int:x>',
                                      **{'Accept': 'text/turtle'}))
        def view(x,):
            return json.dumps({'x':x})

        response = self.c.get('/23', headers={'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23})
        
        response = self.c.get('/23', headers={'Accept':'XXX/turtle'})
        self.assertTrue(response.status_code, 404)

    def test_22(self):
        @self.app.route(match_headers('/<int:x>',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>'}))
        def view(x, max_age,):
            return json.dumps({'x':x,'max_age':max_age})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23, 'max_age':30})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=xx'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/xx', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 404)

    def test_23(self):
        @self.app.route(match_headers('/<int:x>',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>'}))
        def view(x, max_age,):
            return json.dumps({'x':x,'max_age':max_age})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23, 'max_age':30})

        response = self.c.get('/23', headers={'Cache-Control': 'public,\tmax-age=30'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23, 'max_age':30})

    def test_24(self):
        @self.app.route(match_headers('/<int:x>',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>',
                                         'Accept': 'text/*'}))
        def view(x, max_age,):
            return json.dumps({'x':x,'max_age':max_age})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'text/xxx'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23, 'max_age':30})


        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'XXX/turtle'})
        self.assertTrue(response.status_code, 404)


    def test_25(self):
        @self.app.route(match_headers('/<int:x>',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>',
                                         'Accept': 'text/*'}))
        def view(x, max_age,):
            return json.dumps({'x':x,'max_age':max_age})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'text/xxx'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23, 'max_age':30})

        response = self.c.get('/23', headers={'Cache-Control': 'public,\tmax-age=30',
                                              'Accept':'text/xxx'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23, 'max_age':30})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'XXX/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/23', headers={'Cache-Control': 'public,\tmax-age=30',
                                              'Accept':'XXX/turtle'})
        self.assertTrue(response.status_code, 404)

    def test_26(self):
        @self.app.route(match_headers('/<int:x>',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>', 
                                         'Accept': 'text/turtle'}))
        def view(x, max_age,):
            return json.dumps({'x':x,'max_age':max_age})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23, 'max_age':30})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'text/xxx'})
        self.assertTrue(response.status_code, 404)

    def test_27(self):
        @self.app.route(match_headers('/<int:x>',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>',
                                         'Accept': 'text/turtle'}))
        def view(x, max_age,):
            return json.dumps({'x':x,'max_age':max_age})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23, 'max_age':30})

        response = self.c.get('/23', headers={'Cache-Control': 'public,\tmax-age=30',
                                              'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23, 'max_age':30})

        response = self.c.get('/23', headers={'Cache-Control': 'public,\tmax-age=30',
                                              'Accept':'text/xxx'})
        self.assertTrue(response.status_code, 404)

    def test_28(self):
        @self.app.route(match_headers('/<int:x>',
                                      **{'Cache-Control': 'public, max-age=<int:max_age>',
                                         'Accept': 'text/<mime>'}))
        def view(x, max_age, mime,):
            return json.dumps({'x':x,'max_age':max_age,'mime':mime})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23,
                                                              'max_age':30,
                                                              'mime':'turtle'})

        response = self.c.get('/xx', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=xx',
                                              'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 404)

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'XXX/turtle'})
        self.assertTrue(response.status_code, 404)



    def test_29(self):
        @self.app.route(match_headers('/<int:x>',
                                      **{'Cache-Control': 'public,[ \t]max-age=<int:max_age>', 'Accept': 'text/<mime>'}))
        def view(x, max_age, mime,):
            return json.dumps({'x':x,'max_age':max_age,'mime':mime})

        response = self.c.get('/23', headers={'Cache-Control': 'public, max-age=30',
                                              'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23,
                                                              'max_age':30,
                                                              'mime':'turtle'})

        response = self.c.get('/23', headers={'Cache-Control': 'public,\tmax-age=30',
                                              'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode()), {'x':23,
                                                              'max_age':30,
                                                              'mime':'turtle'})

        response = self.c.get('/23', headers={'Cache-Control': 'public, \tmax-age=30',
                                              'Accept':'text/turtle'})
        self.assertTrue(response.status_code, 404)
