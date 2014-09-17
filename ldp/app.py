from flask import Flask
from werkzeug.utils import cached_property
from werkzeug.wsgi import DispatcherMiddleware
from flask.globals import _app_ctx_stack

class NestedFlask(DispatcherMiddleware, Flask):
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

class LdpApp(NestedFlask):

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
