import re
from types import GeneratorType
from collections import deque
from urllib.parse import (
    urlencode,
    urlsplit,
    urlunsplit,
    parse_qs,
    parse_qsl)

from werkzeug.routing import BuildError

from flask import current_app as app
from flask.helpers import url_for as url_for_endpoint


def endpoint_for(ref):
    for rule in app.resource_map._rules:
        match = re.match(rule.rule_re, ref)
        omit_rule = False
        if match is not None:
            args = {}
            for id, value in match.groupdict().items():
                if rule.argmap[id] not in args:
                    args[rule.argmap[id]] = value
                elif not args[rule.argmap[id]] == value:
                    omit_rule = True
            if not omit_rule:
                return rule.endpoint, args
    return None, None


def url_for(ref):
    endpoint, args = endpoint_for(ref)
    if endpoint is not None:
        return url_for_endpoint(endpoint, **args)

    error = BuildError('No endpoint for identifier %r found' % ref, None, None)
    return app.handle_url_build_error(error, None, None)


def wants_rdfsource(request, rdfsource_types=['application/ld+json',
                                              'text/turtle']):
    best = request.accept_mimetypes \
        .best_match(rdfsource_types + ['text/html'])
    return best in rdfsource_types and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


NETLOC_RE = re.compile(
    r'(?:(?P<username>[^:]+)(?::(?P<password>.*))?@)?(?P<hostname>[^:]+)(?::(?P<port>[\d]+))?')

NETLOC_PARAMS = set(('username', 'password', 'hostname', 'port'))

NOT_PROVIDED = object()


class URL(str):
    '''
    Immutable str for url parsing and building

    Basestring operations
    =====================

    ::

        url = URL('http://den:passwd@google.com:2020/path/to?a=2&b=4%23#eee')
        assert(url == u'http://den:passwd@google.com:2020/path/to?a=2&b=4%23#eee')
        assert(url + 'ccc' == u'http://den:passwd@google.com:2020/path/to?a=2&b=4%23#eeeccc')


    Parsing
    =======

    ::
        assert(url.scheme == u'https')
        assert(url.netloc == u'den:passwd@google.com:2020')
        assert(url.username == u'den')
        assert(url.password == u'passwd')
        assert(url.hostname == u'google.com')
        assert(url.port == 2020)
        assert(url.path == u'/path/to')
        assert(url.query == u'a=2&b=4%23')
        assert(url.args == {'a':['2'], 'b':['4#']})
        assert(url.fragment == 'eee')


    Building
    ========
    ::
        assert(url(path='/leads/to/other/place') == u'http://den:passwd@google.com:2020/leads/to/other/place?a=2&b=4%23#eee')

        assert(url(hostname='github.com') == u'http://den:passwd@github.com:2020/leads/to/other/place?a=2&b=4%23#eee')


    but::

    assert(url(netloc='github.com') == u'http://github.com/leads/to/other/place?a=2&b=4%23#eee')

    to change netloc parts - use related netloc attribute names
    (`username`, `password`, `hostname`, `port`)

    same logic with query::

        assert(url(args={'c':22}) == u'http://github.com/leads/to/other/place?c=22#eee')


    or::

        assert(url(query='c=22') == u'http://github.com/leads/to/other/place?c=22#eee')

    To update single query argument::

        assert(url.update_args(c=22) == u'http://github.com/leads/to/other/place??a=2&b=4%23&c=22#eee')

    or::

        assert(url.update_args(('c', 22), d=33) == u'http://github.com/leads/to/other/place??a=2&b=4%23&c=22&e=33#eee')

    '''
    __slots__ = ('_parsed', '_args')

    def __new__(cls, url=None, parsed=None):
        if parsed is not None:
            ret = str.__new__(cls, urlunsplit(parsed))
            ret._parsed = parsed
            return ret

        elif url is not None:
            return str.__new__(cls, url)

        else:
            raise TypeError('`url` or `parsed` ')

    @property
    def parsed(self):
        '''
        for caching purposes
        Use self.[scheme|netloc|...]
        '''
        if getattr(self, '_parsed', None) is None:
            self._parsed = urlsplit(self)
        return self._parsed

    def __call__(self, **kwargs):
        '''builds new url with given urlparse params'''

        if set(kwargs.keys()).intersection(NETLOC_PARAMS):
            username = kwargs.pop('username', NOT_PROVIDED)
            password = kwargs.pop('password', NOT_PROVIDED)
            hostname = kwargs.pop('hostname', NOT_PROVIDED)
            port = kwargs.pop('port', NOT_PROVIDED)

            def replace_netloc_parts(matchobj):

                netloc = dict(((k, v) if v is not None else '')
                              for k, v in matchobj.groupdict().items())

                def extract_part(fresh_value, old_value, prefix=None):
                    if fresh_value is NOT_PROVIDED:
                        if old_value:
                            return (prefix if prefix else '')\
                                + str(old_value)
                        else:
                            return ''
                    elif fresh_value:
                        return (prefix if prefix else '')\
                            + str(fresh_value)
                    else:
                        return ''

                ampersand = any((username,
                                 password,
                                 netloc['username'],
                                 netloc['password']))
                return extract_part(username, netloc['username']) \
                    + extract_part(password, netloc['password'], ':') \
                    + ('@' if ampersand else '') \
                    + extract_part(hostname, netloc['hostname']) \
                    + extract_part(port, netloc['port'], ':')

            kwargs['netloc'] = re.sub(NETLOC_RE,
                                      replace_netloc_parts,
                                      self.parsed.netloc)

        if 'args' in kwargs:
            args = kwargs.pop('args')
            kwargs['query'] = urlencode(args if args else {})

        for name, value in kwargs.items():
            if value is None:
                kwargs[name] = ''

        return URL(parsed=self.parsed._replace(**kwargs))

    def __getattr__(self, name):
        if name in ('_parsed', '_args'):
            return None

        return getattr(self.parsed, name)

    @property
    def args(self):
        '''build and cache `args` dict'''
        if not getattr(self, '_args', None):
            self._args = parse_qs(self.query)

        return self._args

    def update_args(self, *args, **kwargs):
        '''rebuild query and return new URL'''
        current = dict(((k, (v[0] if len(v) == 1 else v))
                        for k, v in parse_qsl(self.query)))
        current.update(dict(args))
        current.update(kwargs)
        return URL(parsed=self.parsed._replace(query=urlencode(current)))


class Pipeline(object):
    '''
    Implements "pipeline" pattern
    '''
    def exit(self, queue):
        while True:
            try:
                queue.append((yield))
            except GeneratorExit:
                return

    def __init__(self, members):
        self.queue = deque()
        self.members = members

    def pipeline(self, *args, **kwargs):
        pipeline = self.exit(self.queue)
        next(pipeline)
        for member in reversed(self.members):
            def _member(func, pipeline):
                while True:
                    try:
                        result = func((yield), *args, **kwargs)
                    except GeneratorExit:
                        pipeline.close()
                        return
                    else:
                        if not isinstance(result, GeneratorType):
                            pipeline.send(result)
                        else:
                            for item in result:
                                pipeline.send(item)

            pipeline = _member(member, pipeline)
            next(pipeline)
        return pipeline

    def __call__(self, items, *args, **kwargs):
        pipeline = self.pipeline(*args, **kwargs)
        for item in items:
            pipeline.send(item)
            if self.queue:
                yield self.queue.popleft()
