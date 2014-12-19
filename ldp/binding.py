
import re
from pprint import pformat

from rdflib import URIRef
from rdflib.namespace import RDF
from rdflib.resource import Resource as RDFResource

from werkzeug.routing import DEFAULT_CONVERTERS, RuleFactory
from werkzeug.local import LocalProxy
from cached_property import cached_property

from . import NS as LDP
from .helpers import wants_rdfsource, Pipeline
from .globals import pool, dataset as ds
from .dataset import DatasetGraphAggregation
from .resource import Resource as LDPResourceApp, TYPES_LIST

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

    def __repr__(self):
        rules = self.iter_rules()
        return '%s(%s)' % (self.__class__.__name__, pformat(list(rules)))

    def endpoint_rules(self, endpoint, args):
        '''
        return rules matched with request or None
         if no rules defined for this endpoint
        '''
        rules = self.get(endpoint)
        if rules is None:
            return

        return self.rules_with_suiteable_args(args, *rules)

    def rules_with_suiteable_args(self, arguments, *rules):
        arguments = set(arguments)
        rules = (rule for rule
                 in rules if arguments.issuperset(rule.arguments))

        rules_by_suiteability\
            = sorted(rules,
                     key=lambda rule: len(arguments.
                                          difference(set(rule.arguments))))
        if len(rules_by_suiteability):
            return rules_by_suiteability


class URIRefBinding(RuleFactory):

    def __init__(self,
                 rule,
                 varname,
                 endpoint,
                 context,
                 map,
                 **options):
        self.rule = rule
        self.varname = varname
        self.endpoint = endpoint
        self.context = context
        self.map = map
        self.options = options

    def uriref(self, **args):
        return URIRef(self.template.format(**args))

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
                argmap[varname] = name
                template += '{%s}' % name
                rule_re += _rule_template % (varname, conv_regex)
                i += 1

        return (rule_re, template, argmap)

    def get_converter(self, variable_name, converter_name, args, kwargs):
        """Looks up the converter for the given parameter.

        .. versionadded:: 0.9
        """
        if not converter_name in self.map.converters:
            raise LookupError('the converter %r does not exist' %
                              converter_name)
        return self.map.converters[converter_name](self.map, *args, **kwargs)

    @property
    def rule_re(self):
        return re.compile(self.parsed_rule[0])

    @property
    def template(self):
        return self.parsed_rule[1]

    @property
    def argmap(self):
        return self.parsed_rule[2]

    @property
    def arguments(self):
        return set(self.argmap.values())

    @cached_property
    def ldp_types(self):
        return self.options.get('types', [])


def remove_from_context(quad, context, is_quad=True):
    if is_quad:
        context.remove(quad)
    else:
        context.remove(quad[:3])
    return quad


class ResourceAppAdapter(object):
    '''
    Resolves rdflib.Resource according to request and map
    Finds resource for `request` and binding map
    Moves resource triples to standalone graph if not moved yet
    '''
    resource_pool = pool
    rdf_resource_class = RDFResource
    resource_app_class = LDPResourceApp
    resource_quad_selectors = [remove_from_context]
    default_ldp_types = [LDP.Resource]

    def __init__(self, map, request):
        self.map = map
        self.request = request
        self.resource_exists = False
        self.bound_with = map.endpoint_rules(self.request.endpoint,
                                             self.request.view_args)
        if self.bound_with is not None:
            self.bound_with = list(self.bound_with)

    @cached_property
    def wants_rdfsource(self):
        return wants_rdfsource(self.request)

    @cached_property
    def binding(self):
        return self._uriref_binding[0]

    @cached_property
    def uriref(self):
        return self._uriref_binding[1]

    @cached_property
    def _uriref_binding(self):
        for binding in self.bound_with:
            ref = binding.uriref(**self.request.view_args)
            if ref is not None:
                return binding, ref

        return None, None

    @cached_property
    def pool(self):
        return [n.identifier for n in self.resource_pool.contexts()]

    @cached_property
    def args(self):
        if self.bound_with is not None:
            self.request.view_args[self.binding.varname] = self.resource
        return self.request.view_args

    def move_to_pool(self, context):
        g = self.resource_pool.graph(self.uriref)
        for ns in ds.namespaces():
            g.bind(*ns)

        if isinstance(context, DatasetGraphAggregation):
            quads = ds.quads((self.uriref, None, None, None))

        else:
            quads = ((s, p, o, context.identifier)
                     for s, p, o in context.triples((self.uriref, None, None)))

        for quad in self.select_quads(quads, context):
            g.add(quad[:3])

        if self.resource_exists:
            return g

    @cached_property
    def resource(self):
        resource = None
        if self.uriref in self.pool:
            resource = self.rdf_resource_class(
                self.resource_pool.graph(self.uriref), self.uriref)
        else:
            g = self.move_to_pool(self.binding.context)
            if g is not None:
                resource = self.rdf_resource_class(g, self.uriref)

        if resource:
            resource.adapter = self

        return resource

    def select_quads(self, quads, context):
        if isinstance(context, LocalProxy):
            context = context._get_current_object()

        if isinstance(context, DatasetGraphAggregation):
            context = ds._get_current_object()

        pipeline = Pipeline(self.resource_quad_selectors)

        for q in pipeline(quads, context, hasattr(context, 'quads')):
            self.resource_exists = True
            yield q

    @cached_property
    def ldp_types(self):
        ldp_types = [o for
                     (s, p, o) in ds[self.resource.identifier:RDF.type:]
                     if o in TYPES_LIST]
        ldp_types.extend(self.binding.ldp_types)
        ldp_types.extend(self.default_ldp_types)
        return list(set(ldp_types))
