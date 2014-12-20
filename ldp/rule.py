from flask import Flask
import re

from werkzeug.routing import (parse_rule,
                              parse_converter_args,
                              RequestAliasRedirect,
                              ValidationError)
from werkzeug._compat import iteritems

import fnmatch


class match_headers(str):
    __slots__ = ('headers', )

    def __new__(cls, path, **headers):
        ret = str.__new__(cls, path)
        ret.headers = headers
        return ret

class HeadersRule(Flask.url_rule_class):

    def match(self, *args, **kwargs):
        match = super(HeadersRule, self).match(*args, **kwargs)
        if hasattr(self.rule, 'headers')\
           and not hasattr(self, '_header_rules_compiled'):
            self.rule.headers = dict(
                                    ((k, self.compile_header_rule(v))
                                     for k, v
                                     in self.rule.headers.items()))
            self._header_rules_compiled = True

        if hasattr(self, 'headers')\
           and hasattr(self.rule, 'headers') and match is not None:
            if not set(self.headers.keys())\
                    .issuperset(set(self.rule.headers.keys())):
                return None

            for header in self.rule.headers:
                header_match = self.rule.headers[
                    header].search(self.headers[header])
                if not header_match:
                    return None
                groups = header_match.groupdict()
                result = {}
                for name, value in iteritems(groups):
                    try:
                        value = self._converters[name].to_python(value)
                    except ValidationError:
                        return
                    result[str(name)] = value
                if self.defaults:
                    result.update(self.defaults)

                if self.alias and self.map.redirect_defaults:
                    raise RequestAliasRedirect(result)
                match.update(result)
        return match

    def compile_header_rule(self, rule):
        """Compiles the regular expression and stores it."""
        assert self.map is not None, 'rule not bound'
        if not '_trace' in self.__dict__:
            self._trace = []
        if not '_converters' in self.__dict__:
            self._converters = {}
        if not '_weights' in self.__dict__:
            self._weights = []
        if not 'arguments' in self.__dict__:
            self.arguments = set()
        regex_parts = []

        def _build_regex(rule):
            for converter, arguments, variable in parse_rule(rule):
                if converter is None:
                    regex_parts.append(fnmatch.translate(variable)[:-7])
                    self._trace.append((False, variable))
                    for part in variable.split('/'):
                        if part:
                            self._weights.append((0, -len(part)))
                else:
                    if arguments:
                        c_args, c_kwargs = parse_converter_args(arguments)
                    else:
                        c_args = ()
                        c_kwargs = {}
                    convobj = self.get_converter(
                        variable, converter, c_args, c_kwargs)
                    regex_parts.append(
                        '(?P<%s>%s)' % (variable, convobj.regex))
                    self._converters[variable] = convobj
                    self._trace.append((True, variable))
                    self._weights.append((1, convobj.weight))
                    self.arguments.add(str(variable))

        # _build_regex(domain_rule)
        # regex_parts.append('\\|')
        self._trace.append((False, '|'))
        _build_regex(rule)
        self._trace.append((False, '/'))
        regex = r'^%s$' % (
            u''.join(regex_parts)
        )
        return re.compile(regex, re.UNICODE)


def header_rule_mixin(cls):
    class HeaderRuleMixin(object):
        def create_url_adapter(self, request):
            adapter = cls.create_url_adapter.__get__(self, cls)(request)
            if request is not None:
                for rule in adapter.map._rules:
                    rule.headers = request.headers
                _match = adapter.match

                def match(self, *args, **kwargs):
                    rv = _match(*args, **kwargs)
                    for rule in adapter.map._rules:
                        del rule.__dict__['headers']
                    return rv
                adapter.match = match.__get__(adapter, adapter.__class__)
            return adapter
    return HeaderRuleMixin
