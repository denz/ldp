import unittest
from random import randint
from flask import request, current_app, url_for
from flask.globals import _app_ctx_stack
from flask import Flask
from treelib import Tree
from ldp.app import NestedFlask, NestedFlaskMapping

METHODS = ('GET', 'PATCH', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'TRACE',)


def getleaf():
    leafname = __name__ + str(randint(1, 100000))
    leaf = Flask(leafname)

    @leaf.route('/', methods=METHODS)
    def oleaf():
        return 'LEAF %s:%s:%s' % (current_app.name,
                                  request.path, url_for('xleaf'))

    @leaf.route('/x', methods=METHODS)
    def xleaf():
        return 'SUBSUB %s:%s:%s ' % (current_app.name,
                                     request.path,
                                     url_for('oleaf'))

    @leaf.route('/z', methods=METHODS)
    def zleaf():
        return 'context depth %s ' % (len([stack.app for stack
                                           in _app_ctx_stack._local.stack]))

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


TREE = {
    ('/root', 'root_id'): {
        ('/x', 'x_id'): {
            ('/xx1', 'xx1_id'): {},
            ('/xx2', 'xx2_id'): {},
        },
        ('/y', 'y_id'): {
            ('/yy1', 'yy1_id'): {},
            ('/yy2', 'yy2_id'): {},
        },
        ('/z', 'z_id'): {
            ('/zz1', 'zz1_id'): {
                ('/zzz1', 'zzz1_id'): {}
            },
            ('/zz2', 'zz2_id'): {},
        }
    }
}


def gentree(tree=Tree(), treedef=TREE, parent=None):
    for k, v in treedef.items():
        if parent is not None:
            k = k + (parent,)
        tree.create_node(*k)
        gentree(tree=tree, treedef=v, parent=k[1])
    return tree

generated_nodes = []
def flask_node(node):
    app = Flask(node.identifier)
    generated_nodes.append(node.identifier)

    @app.route('/', methods=('GET',))
    def view():
        return '%s:%s' % (node.identifier,
                          [stack.app for stack in _app_ctx_stack._local.stack])
    return app


def app_constructor(tree, node):
    subs = tree.children(node.identifier)
    nested = NestedFlask(
        flask_node(node),
        NestedFlaskMapping(tree, subs, app_constructor))
    return nested


class TestNestedWithTreeLib(unittest.TestCase):

    def setUp(self):
        global generated_nodes
        generated_nodes = []

        print()
        self.tree = gentree()
        root = self.tree.get_node('root_id')
        subs = self.tree.children('root_id')
        self.app = NestedFlask(
            flask_node(root),
            NestedFlaskMapping(self.tree, subs, app_constructor))

        self.c = self.app.test_client()

    def urls(self):
        _urls = []
        for path in self.tree.paths_to_leaves():
            path = [self.tree.get_node(nid).tag for nid in path]
            for i in range(len(path)):
                url = ''.join(path[1:i + 1])
                if not url in _urls:
                    _urls.append(url)
        return sorted(_urls)

    def test_nested_generation(self):
        # print (self.tree.children('root_id'))
        for url in self.urls():
            self.assertEqual(self.c.get(url).status_code, 200)

        for url in self.urls():
            self.c.get(url)

        self.assertEqual(len(generated_nodes), len(set(generated_nodes)))