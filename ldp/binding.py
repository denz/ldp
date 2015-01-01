
import re
from werkzeug.routing import DEFAULT_CONVERTERS
from rdflib import URIRef
from cached_property import cached_property

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


class URIRefBinding(object):
    '''
    Behaves much like `werkzeug.routing.RuleFactory`
    Creates uriref matching regexp
    formats and converts uriref and its vars according to rule
    matches uriref
    holds binding arguments list
    '''
    def __init__(self,
                 rule,
                 map,
                 **options):
        self.rule = rule
        self.map = map
        self.options = options

    def uriref(self, **args):
        return URIRef(self.template.format(**args))

    @cached_property
    def parsed_rule(self):
        rule_re = ''
        template = ''
        argmap = {}
        i = 0
        for part in iter_rule_parts(self.rule, converters=self.map.converters):
            if isinstance(part, str):
                rule_re += re.escape(part)
                template += part
            else:
                name, args, converter = part
                converter = self\
                    .map.converters.get(part[2],
                                        self.map.converters['default'])
                conv_regex = converter.regex
                exclusion = None
                exclusion = re.match(r'\[(.*\/.*)\]', conv_regex)
                if exclusion:
                    exclusion = exclusion.groups()[0]
                    if not '<' in exclusion:
                        exc_pos = conv_regex.find(exclusion) + len(exclusion)
                        conv_regex = conv_regex[:exc_pos]\
                            + '<' + conv_regex[exc_pos:]
                varname = 'id%s' % i
                argmap.setdefault(name, []).append(varname)
                template += '{%s}' % name
                rule_re += _rule_template % (varname, conv_regex)
                i += 1

        return (rule_re, template, argmap)

    def get_converter(self, variable_name, converter_name, args, kwargs):
        if not converter_name in self.map.converters:
            raise LookupError('the converter %r does not exist' %
                              converter_name)
        return self.map.converters[converter_name](self.map, *args, **kwargs)

    @property
    def re(self):
        return re.compile(self.parsed_rule[0])

    @property
    def template(self):
        return self.parsed_rule[1]

    @property
    def argmap(self):
        return self.parsed_rule[2]

    @property
    def arguments(self):
        return set(self.argmap.keys())

    def match_uriref(self, uriref):
        match = self.re.match(uriref)
        if not match:
            return

        match = match.groupdict()
        rv = {}
        for argname, argids in self.argmap.items():
            rv[argname] = match[argids[0]]
            for argid in argids[1:]:
                if match[argid] != rv[argname]:
                    return

        return rv
