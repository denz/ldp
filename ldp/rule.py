from flask import Flask
import re
from collections import defaultdict


from rdflib import URIRef
from werkzeug.routing import DEFAULT_CONVERTERS, RuleFactory
from werkzeug.routing import (Map,
                              parse_rule,
                              parse_converter_args,
                              RequestAliasRedirect,
                              ValidationError, Rule)
from werkzeug._compat import iteritems
from flask.helpers import locked_cached_property as cached_property
import fnmatch


_uriref_rule_re = re.compile(r'''
    (?P<head>[^<]*)                           # static rule data
    <
    (?:
        (?P<converter>[a-zA-Z_][a-zA-Z0-9_]*)   # converter name
        (?:\((?P<args>.*?)\))?                  # converter arguments
        \:                                      # variable delimiter
    )?
    (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)        # variable name
    >
    (?P<tail>.*)                           # tail of rule
''', re.VERBOSE)


_rule_template = r'(?P<%s>%s)'


def iter_rule_parts(rule, converters=DEFAULT_CONVERTERS):
    while rule:
        match = re.match(_uriref_rule_re, rule)
        if not match:
            break
        group = match.groupdict()
        if group['head']:
            yield group['head']
        yield (group['variable'], group['args'], group['converter'])
        rule = group['tail']
    yield rule


class match_headers(str):
    __slots__ = ('headers', )

    def __new__(cls, path, **headers):
        ret = str.__new__(cls, path)
        ret.headers = headers
        return ret


class HeadersRule(Flask.url_rule_class):

    def match(self, *args, **kwargs):
        match = super(HeadersRule, self).match(*args, **kwargs)
        if hasattr(self.rule, 'headers') and match is not None:
            if not hasattr(self, '_header_rules_compiled'):
                self.rule.headers = dict(((k, self.compile_header_rule(v))
                                          for k, v in self.rule.headers.items()))
                self._header_rules_compiled = True
            if not set(self.headers.keys()).issuperset(set(self.rule.headers.keys())):
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


class with_context(str):
    __slots__ = ('name', 'context')

    def __new__(cls, ref, name, context=None):
        ret = str.__new__(cls, ref)

        ret.name = name
        ret.context = context

        return ret


class ResourceMap(object):
    default_converters = DEFAULT_CONVERTERS

    def __init__(self, rules=(), converters=None):
        self._rules = []
        self._rules_by_endpoint = {}

        self.converters = self.default_converters.copy()
        if converters:
            self.converters.update(converters)

        for rulefactory in rules:
            self.add(rulefactory)

    def iter_rules(self, endpoint=None):
        """Iterate over all rules or the rules of an endpoint.

        :param endpoint: if provided only the rules for that endpoint
                         are returned.
        :return: an iterator
        """
        if endpoint is not None:
            return iter(self._rules_by_endpoint[endpoint])
        return iter(self._rules)

    def add(self, rulefactory):
        """Add a new rule or factory to the map and bind it.  Requires that the
        rule is not bound to another map.

        :param rulefactory: a :class:`Rule` or :class:`RuleFactory`
        """
        for rule in rulefactory.get_rules(self):
            self._rules.append(rule)
            self._rules_by_endpoint.setdefault(rule.endpoint, []).append(rule)

    def get(self, endpoint):
        return self._rules_by_endpoint.get(endpoint, None)


    def endpoint_rules(self, endpoint, args):
        rules = self.get(endpoint)
        if rules is None:
            return rules

        return (rule for rule in self.suiteable_rules(args, *rules))

    def suiteable_rules(self, arguments, *rules):
        arguments = set(arguments)
        rules = (rule for rule 
                    in rules if arguments.issuperset(rule.arguments))

        rules_by_suiteability = sorted(rules,
                        key=lambda rule: len(arguments.difference(set(rule.arguments))))
        if len(rules_by_suiteability):
            return rules_by_suiteability

class URIRefRule(RuleFactory):
    def __init__(self, rule, varname, endpoint, context, map, **options):
        self.rule = rule
        self.varname = varname
        self.endpoint = endpoint
        self.context = context
        self.map = map

    def resource(self, **args):
        return self.context.resource(URIRef(self.template.format(**args)))

    def get_rules(self, map):
        yield self

    @cached_property
    def parsed_rule(self):
        rule_re = ''
        template = ''
        argmap = {}
        i = 0
        for part in iter_rule_parts(self.rule):
            if isinstance(part, str):
                rule_re += re.escape(part)
                template += part
            else:
                name, args, converter = part
                converter = self.map.converters.get(part[2], self.map.converters['default'])
                conv_regex = converter.regex
                exclusion = None
                exclusion = re.match(r'\[(.*\/.*)\]', conv_regex)
                if exclusion:
                    exclusion = exclusion.groups()[0]
                    if not '<' in exclusion:
                        exc_pos = conv_regex.find(exclusion) + len(exclusion)
                        conv_regex = conv_regex[:exc_pos] + '<' + conv_regex[exc_pos:]
                varname = 'id%s'%i
                argmap.setdefault(name, []).append(varname)
                template += '{%s}'%name
                rule_re += _rule_template%(varname, conv_regex)
                i += 1

        return (re.compile(rule_re), template, argmap)

    def get_converter(self, variable_name, converter_name, args, kwargs):
        """Looks up the converter for the given parameter.

        .. versionadded:: 0.9
        """
        if not converter_name in self.map.converters:
            raise LookupError('the converter %r does not exist' % converter_name)
        return self.map.converters[converter_name](self.map, *args, **kwargs)

    @property
    def rule_re(self):
        return self.parsed_rule[0]

    @property
    def template(self):
        return self.parsed_rule[1]

    @property
    def argmap(self):
        return self.parsed_rule[2]

    @property
    def arguments(self):
        return self.argmap.keys()