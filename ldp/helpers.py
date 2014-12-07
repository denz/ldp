import re

from werkzeug.routing import BuildError

from flask import current_app as app, request
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

    error = BuildError('No endpoint for identifier %r found'%ref, None, None)
    return app.handle_url_build_error(error, None, None)
