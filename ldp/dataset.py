from contextlib import contextmanager
from rdflib.graph import ReadOnlyGraphAggregate, Graph

from .globals import _dataset_ctx_stack

@contextmanager
def context(*graph_descriptors):
    graphs = {}
    for descriptor in graph_descriptors:
        g = Graph(identifier=descriptor.get('id', None))
        if 'path' in descriptor:
            g.parse(descriptor['path'], format=descriptor.get('format', 'turtle'))
        graphs[descriptor.get('name', None)] = g

    ds = ReadOnlyGraphAggregate(list(graphs.values()))
    ds._aggregated_graphs = {}
    for name, graph in graphs.items():
        ds._aggregated_graphs[name] = graph
    try:
        _dataset_ctx_stack.push(ds)
        yield ds
    finally:
        _dataset_ctx_stack.pop()
