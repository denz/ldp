from treelib import Tree
from rdflib.namespace import *

from .url import URL
from . import NS as LDP

class Tree(Tree):
    pass


class TreeRootsNormalizer(object):

    """
    Primitive resource_tree_builder
    Normalizes incoming graphs by setting LDP schema objects to calculated root resources
    iterates over normalized resources
    """
    tree_class = Tree

    def __init__(self, p, o):
        self.subjects = (p, o)

    def tree(self, graph, hostname, root_id='root', root_url='/'):
        """
        Builds resource tree
        """
        tree = self.tree_class()
        tree.create_node(root_url, root_id, data=graph)
        for resource in self(graph, hostname):
            resource.add(RDF.type, LDP.Resource)
            tree.create_node(resource.parsed.path,
                             resource.identifier,
                             root_id,
                             data=resource)
        return tree

    def __call__(self, graph, hostname):
        for subject in graph.subjects(*self.subjects):
            parsed = URL(subject)
            if parsed.hostname == hostname:
                resource = graph.resource(subject)
                resource.parsed = parsed
                yield resource
