from contextlib import contextmanager
from itertools import chain
from rdflib.graph import (
    ReadOnlyGraphAggregate, Dataset, Graph, ConjunctiveGraph)

from rdflib.paths import Path

from .globals import _dataset_ctx_stack


class DatasetGraphAggregation(ReadOnlyGraphAggregate):

    def __init__(self, graphs, store='default'):
        if store is not None:
            super(ReadOnlyGraphAggregate, self).__init__(store)
            Graph.__init__(self, store)
            self.__namespace_manager = None

        self.graphs = graphs

    def triples(self, xxx_todo_changeme8):
        (s, p, o) = xxx_todo_changeme8
        graphs = chain(*(g.contexts() if isinstance(g, Dataset)
                         else (g,) for g in self.graphs))
        for graph in graphs:
            if isinstance(p, Path):
                for s, o in p.eval(self, s, o):
                    yield s, p, o
            else:
                for s1, p1, o1 in graph.triples((s, p, o)):
                    yield (s1, p1, o1)


class GraphGetter(object):

    def __init__(self, ds=None):
        self.ds = ds
        self.map = {}
        self.aggregation = DatasetGraphAggregation(self.map.values())

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if not 'g' in instance.__dict__:
            instance.g = GraphGetter(ds=instance)

        return instance.g

    def __getitem__(self, name):
        if name is None:
            return self.ds.graph()
        return self.map[name]

    def __setitem__(self, name, identifier):
        self.map[name] = self.ds.graph(identifier)
        return self.map[name]


def _push_dataset_ctx(**graph_descriptors):
    ds = NamedContextDataset()
    ds.g['resources'] = Dataset()
    for name, descriptor in graph_descriptors.items():
        if set(descriptor).intersection(set(('data', 'file', 'source'))):
            ds.g[name] = ds.parse(**descriptor)
        else:
            ds.g[name] = ConjunctiveGraph()
    _dataset_ctx_stack.push(ds)
    return ds


def _pop_dataset_ctx():
    _dataset_ctx_stack.pop()


class NamedContextDataset(Dataset):
    g = GraphGetter()


@contextmanager
def context(**graph_descriptors):

    try:

        yield _push_dataset_ctx(**graph_descriptors)
    finally:
        _pop_dataset_ctx()
