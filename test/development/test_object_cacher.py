from unittest import TestCase
from ldp.helpers import Uncacheable
from cached_property import cached_property


class Uncache(Uncacheable):
    @cached_property
    def test1(self):
        return sum(range(10))

u = Uncache()

class TestUncache(TestCase):
    def test_uncaching(self):
        u.test1
        self.assertIn('test1', u.__dict__)
        u.uncache()
        self.assertNotIn('test1', u.__dict__)
        u.test1
        self.assertIn('test1', u.__dict__)
        u.uncache()
        self.assertNotIn('test1', u.__dict__)        