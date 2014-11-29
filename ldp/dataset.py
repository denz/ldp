from contextlib import contextmanager
from rdflib.graph import ReadOnlyGraphAggregate, Dataset, Graph

from .globals import _dataset_ctx_stack


class DatasetGraphAggregation(ReadOnlyGraphAggregate):
    def __init__(self, valuesview, store='default'):
        if store is not None:
            super(ReadOnlyGraphAggregate, self).__init__(store)
            Graph.__init__(self, store)
            self.__namespace_manager = None

        self.graphs = valuesview

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


class NamedContextDataset(Dataset):
    g = GraphGetter()

@contextmanager
def context(**graph_descriptors):
    ds = NamedContextDataset()
    for name, descriptor in graph_descriptors.items():
        ds.g[name] = ds.parse(**descriptor)
    try:
        _dataset_ctx_stack.push(ds)
        yield ds
    finally:
        _dataset_ctx_stack.pop()
