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

    def tree(self, graph, root_url):
        """
        Builds resource tree
        """
        root_url = URL(root_url)
        tree = self.tree_class()
        tree.create_node(root_url.path, root_url, data=graph)
        for resource in self(graph, root_url):
            resource.add(RDF.type, LDP.Resource)
            tree.create_node(resource.parsed.path,
                             resource.identifier,
                             root_url,
                             data=resource)
        return tree

    def __call__(self, graph, root_url):
        for subject in graph.subjects(*self.subjects):
            if subject.startswith(root_url):

                resource = graph.resource(subject)
                resource.parsed = URL(subject)
                yield resource
