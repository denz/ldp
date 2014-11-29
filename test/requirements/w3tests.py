#!/usr/bin/env python
import sys
from os import path
import os
import argparse
import urllib.request
from types import ModuleType
from collections import OrderedDict
from inspect import cleandoc

import ast
from codegen import SourceGenerator
from lxml import html
from slugify import slugify
import html2text
HTMLCONVERTER = html2text.HTML2Text()
HTMLCONVERTER.ignore_links = False
html2text = HTMLCONVERTER.handle

class SourceGenerator(SourceGenerator):
    def visit_arg(self, node):
        self.write(node.arg)

def get_argparser():
    parser = argparse.ArgumentParser(description='Update tests with LDPR docs')
    parser.add_argument('--url', type=str,
                        help='rfc url',
                        default='http://www.w3.org/TR/2014/WD-ldp-20140916/',
                        )
    parser.add_argument('--rfc2119-class', type=str,
                        help='rfc2119 requirement classes',
                        nargs='+',
                        default=['MUST', 'SHOULD'])

    parser.add_argument('--testbases', type=str,
                        help='Bases for tests',
                        nargs='+',
                        default=['LdpTestCase',])

    parser.add_argument('--path', type=str,
                        help='modules path',
                        default=path.abspath(path.dirname(__file__)))

    parser.add_argument('--header', type=str,
                        help='modules path',
                        default='from test.requirements.base import LdpTestCase')

    return parser


class AppendDocToMethods(ast.NodeTransformer):
    def __init__(self, testmethods):
        super(AppendDocToMethods, self).__init__()
        self.testmethods = testmethods

    def visit_FunctionDef(self, node):
        if node.name in self.testmethods:
            rewrite_doc(node, self.testmethods[node.name])
            del self.testmethods[node.name]

        return node

def get_doc_nodes(doc):
    return [ast.Expr(value=ast.Name('"""', ast.Load())),
            ast.Expr(value=ast.Name(cleandoc(doc).replace('\t', ''), ast.Load())),
            ast.Expr(value=ast.Name('"""', ast.Load()))]

def rewrite_doc(node, doc):
    doc_nodes = get_doc_nodes(doc)
    original_docstring = ast.get_docstring(node)
    if original_docstring is not None:
        node.body = node.body[1:]
    for doc_node in reversed(doc_nodes):
        node.body.insert(0, doc_node)


def cases_dict(section, required_types):
    testcases = OrderedDict()   
    rfc2119_types = ' or '.join(['@title="%s"'%st for st in required_types])

    for testmethod in section.xpath('.//section[h5[em[@class="rfc2119"][%s]]]'%rfc2119_types):
        casename = ''.join((subname.capitalize() 
                            for subname 
                            in slugify(testmethod.xpath('../@id').pop()).split('-')))
        if not casename in testcases:
            testcases[casename] = OrderedDict()
        testname = 'test_%s'%testmethod.xpath('.//span[@class="secno"]/text()')[0].strip().replace('.', '_')
        testcases[casename][testname] = testmethod.text_content()
    return testcases


def create_testmethod(name, doc):
    method_node = ast.FunctionDef(name=name,
                                  args=ast.arguments(
                                  args=[ast.arg(arg='self', annotation='self')], 
                                  vararg=None,
                                  varargannotation=None,
                                  kwonlyargs=[],
                                  kwarg=None,
                                  kwargannotation=None, 
                                  defaults=[],
                                  kw_defaults=[]),
                                  body=get_doc_nodes(doc)+[Pass(),],
                                  decorator_list=[],
                                  returns=None)
    # print(to_source(method_node))
    return method_node

def to_source(node, indent_with=' ' * 4, add_line_information=False):
    generator = SourceGenerator(indent_with, add_line_information)
    generator.visit(node)
    def node_repr(node):
        if isinstance(node, str):
            return node
        if isinstance(node, ast.alias):
            return node.name
    return ''.join([node_repr(r) for r in generator.result])

def update_module_with_section(module_node, section, section_types, testbases):
    section_html = html.tostring(section).decode()
    doc = html2text(section_html)
    rewrite_doc(module_node, doc)
    testcases = cases_dict(section, section_types)

    for node in module_node.body[3:]:
        if isinstance(node, ast.ClassDef) and node.name in testcases:
            #rewrite docs for existing methods in existing case
            docs_transformer = AppendDocToMethods(testcases[node.name])
            docs_transformer.visit(node)

            #append uncreated methods to existing case
            for (testmethod, doc) in docs_transformer.testmethods.items():

                node.body.append(create_testmethod(testmethod, doc))

            del testcases[node.name]
    #create uncreated testcases
    for testcase, testmethods in testcases.items():
        if not testmethods:
            continue

        casedef = ast.ClassDef( name=testcase,
                                body=[],
                                bases=(ast.Name(base, ast.Load()) for base in testbases),
                                decorator_list=[])
        for testmethod, doc in testmethods.items():
            casedef.body.append(create_testmethod(testmethod, doc))
        module_node.body.append(casedef)

    return module_node


def main(args=sys.argv[1:], argparser=get_argparser()):

    args = argparser.parse_args(args)
    print (args)
    opener = urllib.request.build_opener()
    # opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    with opener.open(args.url) as response:
        et = html.parse(response)
        sections = []
        for chapterid in ('ldpr', 'ldpc'):
            sections.extend(et.xpath('//section[@id="%s"]/section[@class=not("informative")]'%chapterid))

        for section in sections:
            module_name = 'test_%s'%slugify(section.xpath('./h3')[0]\
                                            .text_content().split(' ', 1)[1])\
                                            .replace('-','_')
            try:
                existing_test_module = __import__(module_name)
                with open(existing_test_module.__file__, 'r') as module_file:
                    module_source = module_file.read()
            except ImportError as e:
                if e._not_found:
                    module_source = args.header
                else:
                    raise e
            module_node = ast.parse(module_source)
            module_node = update_module_with_section(module_node,
                                                     section,
                                                     args.rfc2119_class,
                                                     args.testbases)

            with open(path.join(args.path, '%s.py'%module_name), 'wb') as module_file:
                module_file.write(bytes(to_source(module_node), 'utf8'))

from ast import *

def dump(node, annotate_fields=True, include_attributes=False, indent=' '):
    """
    Return a formatted dump of the tree in *node*.  This is mainly useful for
    debugging purposes.  The returned string will show the names and the values
    for fields.  This makes the code impossible to evaluate, so if evaluation is
    wanted *annotate_fields* must be set to False.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    *include_attributes* can be set to True.
    """

    def _format(node, level=0):
        if isinstance(node, AST):
            fields = [(a, _format(b, level)) for a, b in iter_fields(node)]
            if include_attributes and node._attributes:
                fields.extend([(a, _format(getattr(node, a), level))
                               for a in node._attributes])
            return ''.join([
                node.__class__.__name__,
                '(',
                ', '.join(('%s=%s' % field for field in fields)
                           if annotate_fields else
                           (b for a, b in fields)),
                ')'])
        elif isinstance(node, list):
            lines = ['[']
            lines.extend((indent * (level + 2) + _format(x, level + 2) + ','
                         for x in node))
            if len(lines) > 1:
                lines.append(indent * (level + 1) + ']')
            else:
                lines[-1] += ']'
            return '\n'.join(lines)
        return repr(node)

    if not isinstance(node, AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    return _format(node)

def parseprint(code, filename="<string>", mode="exec", **kwargs):
    """Parse some code from a string and pretty-print it."""
    node = parse(code, mode=mode)   # An ode to the code
    print(dump(node, **kwargs))

ccc = """
class A(object):
    def test_method(self, x):
        pass
"""
if __name__ == '__main__':
    main()
    # parseprint(ccc)