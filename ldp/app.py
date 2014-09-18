from flask import Flask
from werkzeug.utils import cached_property
from werkzeug.wsgi import DispatcherMiddleware
from flask.globals import _app_ctx_stack


class NestedFlask(DispatcherMiddleware, Flask):
    """Nested applications dispatcher.
    Same as :class:`werkzeug.DispatcherMiddleware` but proxies root application
    methods.

    This allows to create deep nested application trees 
    """
    def __call__(self, environ, start_response):
        script = environ.get('PATH_INFO', '')
        path_info = ''
        while '/' in script:
            if script in self.mounts:
                app = self.mounts[script]
                break
            items = script.split('/')
            script = '/'.join(items[:-1])
            path_info = '/%s%s' % (items[-1], path_info)
        else:
            app = self.mounts.get(script, self.app)
        original_script_name = environ.get('SCRIPT_NAME', '')
        environ['SCRIPT_NAME'] = original_script_name + script
        environ['PATH_INFO'] = path_info
        if self.app != app:
            with self.app.app_context():
                return app(environ, start_response)
        else:
            return app(environ, start_response)

    def __getattr__(self, name):
        self.__dict__[name] = getattr(self.app, name)
        return self.__dict__[name]

class NestedFlaskMapping(dict):
    """Generates :class:`treelib.Tree` based mapping for nested flask recursively on the fly
    """
    def __init__(self, tree, nodes, constructor, *args, **kwargs):
        self.nodes = nodes
        self.nested_tags = [node.tag for node in nodes]
        self.tree = tree
        self.constructor = constructor
        super(NestedFlaskMapping, self).__init__(*args, **kwargs)

    def __getitem__(self, tag):
        if super(NestedFlaskMapping, self).__contains__(tag):
            return super(NestedFlaskMapping, self).__getitem__(tag)

        if not tag in self.nested_tags:
            raise KeyError(tag)

        app = self.constructor(self.tree,
                               self.nodes[self.nested_tags.index(tag)])
        super(NestedFlaskMapping, self).__setitem__(tag, app)

        return super(NestedFlaskMapping, self).__getitem__(tag)

    def __iter__(self):
        for nid in self.nested_tags:
            self[nid]
            yield nid

    def __len__(self):
        return len(self.nodes)

    def __contains__(self, tag):
        if not super(NestedFlaskMapping, self).__contains__(tag):
            return tag in self.nested_tags
        return True

class LdpApp(NestedFlask):
    """Test App docs
    """
    @cached_property
    def storage(self):
        storage = self.config['STORAGE']


def Ldp(*args, app=None, storage=None, **options):
    '''
    Creates ldp application or generates resource views for existing
    '''
    if app is None:
        app = LdpApp(*args, **options)
    app.config.setdefault('STORAGE', storage)
    return app
