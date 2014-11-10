from treelib import Tree
from rdflib.namespace import *
from .url import URL
from . import NS as LDP


class TreeRootsNormalizer(object):

    """
    Primitive resource_tree_builder
    Normalizes incoming graphs by setting LDP schema objects to calculated root resources
    iterates over normalized resources
    """
    tree_class = Tree

    def __init__(self, p, o):
        self.subjects = (p, o)

    def tree(self, graph, root_resource):
        """
        Builds resource tree
        """
        root_id = root_resource.identifier
        root_url = URL(root_resource.identifier)
        path = root_url.path if root_url.path else '/'
        root_url = root_url(path=path)
        tree = self.tree_class()
        tree.create_node(path,
                         root_id,
                         data=root_resource)
        for resource in self.roots(graph, root_url):
            tree.create_node(resource.parsed.path,
                             resource.identifier,
                             root_id,
                             data=resource)
        return tree

    def roots(self, graph, root_url):
        for subject in graph.subjects(*self.subjects):
            if subject.startswith(root_url):

                resource = graph.resource(subject)
                resource.parsed = URL(subject)
                yield resource
