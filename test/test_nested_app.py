from ldp.app import NestedFlask
from flask import Flask
import unittest
from collections import Mapping
from flask import request, current_app, url_for
from flask.globals import _app_ctx_stack
import traceback
from pprint import pprint

from random import randint

METHODS = ('GET', 'PATCH', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'TRACE',)


def getleaf():
    leafname = __name__ + str(randint(1, 100000))
    leaf = Flask(leafname)

    @leaf.route('/', methods=METHODS)
    def oleaf():
        return 'LEAF %s:%s:%s' % (current_app.name, request.path, url_for('xleaf'))

    @leaf.route('/x', methods=METHODS)
    def xleaf():
        return 'SUBSUB %s:%s:%s ' % (current_app.name, request.path, url_for('oleaf'))

    @leaf.route('/z', methods=METHODS)
    def zleaf():
        return 'context depth %s ' % (len([stack.app for stack in _app_ctx_stack._local.stack]))

    return leaf

root = Flask(__name__)


@root.route('/', methods=METHODS)
def rootpage():
    return 'ROOT'


@root.route('/c', methods=METHODS)
def cleaf():
    return 'CROOTLEAF'


@root.route('/a', methods=METHODS)
def aleaf():
    return 'AROOTLEAF'


@root.route('/zz', methods=METHODS)
def zzleaf():
    appstack = [stack.app for stack in _app_ctx_stack._local.stack]
    return 'context depth %s %s' % (len(appstack), appstack)

class TestNestedFlask(unittest.TestCase):
    app_class = NestedFlask
    app_map = {
        '/a': getleaf(),
        '/b': getleaf()
    }

    def setUp(self):
        self.app = self.app_class(root, self.app_map)
        self.c = self.app.test_client()

    def test_root_urls(self):
        for method in METHODS:
            response = self.c.open('/', method=method)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'ROOT', response.data)

        for method in METHODS:
            response = self.c.get('/c')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'CROOTLEAF', response.data)

        for method in METHODS:
            response = self.c.get('/a')
            self.assertNotIn(b'AROOTLEAF', response.data)

        for method in METHODS:
            response = self.c.get('/x')
            self.assertEqual(response.status_code, 404)

    def test_sub_urls(self):
        for method in METHODS:
            for mount in ('/a', '/b'):
                response = self.c.open(mount, method=method)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'LEAF', response.data)

                response = self.c.open(mount + '/x', method=method)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'SUBSUB', response.data)

                response = self.c.open(mount + '/y', method=method)
                self.assertEqual(response.status_code, 404)

                response = self.c.open(mount + '/x/y', method=method)
                self.assertEqual(response.status_code, 404)

    def test_app_context(self):
        for url, app in self.app_map.items():
            response = self.c.get(url)
            print(app.name, response.data)
            self.assertIn(bytes(app.name, 'ascii'), response.data)

    def test_url_for(self):
        response = self.c.get('/a')
        self.assertIn(b':/:/a/x', response.data)
        print()
        print(response.data)

        response = self.c.get('/a/x')
        self.assertIn(b':/x:/a/', response.data)
        print(response.data)

    def test_app_context_stack(self):
        response = self.c.get('/a/z')
        self.assertIn(b'2', response.data)
        print(response.data)

        response = self.c.get('/zz')
        self.assertIn(b'1', response.data)
        print(response.data)