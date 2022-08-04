import unittest
from itertools import product

from lark import Tree
from lark.visitors import CollapseAmbiguities
from lark_ambig_tools import CountTrees, Disambiguator, _lazy_product


class TestCountedTree(unittest.TestCase):

    def test_unambiguous_tree(self):
        tree = Tree("start", ["A", Tree("b", ["B"]), Tree("c", []), "D"])
        counted_tree = CountTrees().transform(tree)
        self.assertEqual(counted_tree.derivation_count, 1)
        self.assertEqual(counted_tree.children[1].derivation_count, 1)
        self.assertEqual(counted_tree.children[2].derivation_count, 1)

    def test_top_level_ambiguity(self):
        tree = Tree("_ambig", [Tree("start", ["a"]), Tree("start", ["b"])])
        counted_tree = CountTrees().transform(tree)
        self.assertEqual(counted_tree.derivation_count, 2)
        self.assertEqual(counted_tree.children[0].derivation_count, 1)
        self.assertEqual(counted_tree.children[1].derivation_count, 1)

    def test_lower_lever_ambiguity(self):
        tree = Tree("start", [Tree("_ambig", [Tree("a", []), Tree("b", [])])])
        counted_tree = CountTrees().transform(tree)
        self.assertEqual(counted_tree.derivation_count, 2)
        self.assertEqual(counted_tree.children[0].derivation_count, 2)
        self.assertEqual(counted_tree.children[0].children[0].derivation_count, 1)
        self.assertEqual(counted_tree.children[0].children[1].derivation_count, 1)

    def test_mixed_ambiguity(self):
        tree = Tree("start", [Tree("_ambig", [Tree("a", []), Tree("b", [])]),
                              Tree("_ambig", [Tree("c", []), Tree("d", []), Tree("e", [])]),
                              Tree("h", []),
                              Tree("_ambig", [Tree("f", []), Tree("g", [])])])
        counted_tree = CountTrees().transform(tree)
        self.assertEqual(counted_tree.derivation_count, 12)
        self.assertEqual(counted_tree.children[0].derivation_count, 2)
        self.assertEqual(counted_tree.children[1].derivation_count, 3)
        self.assertEqual(counted_tree.children[3].derivation_count, 2)

    def test_nested_ambiguity(self):
        tree = Tree("_ambig", [Tree("s", [Tree("_ambig", [Tree("a", []), Tree("b", []), Tree("c", [])]), "F"]),
                               Tree("s", [Tree("_ambig", [Tree("d", []), Tree("e", [])]), "G"])])
        counted_tree = CountTrees().transform(tree)
        self.assertEqual(counted_tree.derivation_count, 5)
        self.assertEqual(counted_tree.children[0].derivation_count, 3)
        self.assertEqual(counted_tree.children[1].derivation_count, 2)

    def test_deeply_nested_ambiguity(self):
        nested_tree = Tree("_ambig", [Tree("s", [Tree("_ambig", [Tree("a", []), Tree("b", []), Tree("c", [])]), "F"]),
                               Tree("s", [Tree("_ambig", [Tree("d", []), Tree("e", [])]), "G"])])
        tree = Tree("_ambig", [Tree("start", [Tree("_ambig", [
                Tree("a", [Tree("_ambig", [Tree("_ambig", [Tree("a", []), Tree("b", [])])])]),
                Tree("b", [nested_tree])]),
            ]),
                Tree("start", [Tree("_ambig", [Tree("d", []), Tree("e", [])]), nested_tree])])
        counted_tree = CountTrees().transform(tree)
        self.assertEqual(counted_tree.derivation_count, 17)
        self.assertEqual(counted_tree.children[0].derivation_count, 7)
        self.assertEqual(counted_tree.children[1].derivation_count, 10)


class TestLazyProduct(unittest.TestCase):

    def test_single_iterable(self):
        iterable = [1, 4, 5, 2, 6]
        lprod = list(_lazy_product([iterable], [len(iterable)]))
        prod = list(product(iterable))
        self.assertListEqual(lprod, prod)

    def test_two_iterables(self):
        lprod = list(_lazy_product([range(5), range(2)], [5, 2]))
        prod = list(product(range(5), range(2)))
        self.assertListEqual(lprod, prod)

    def test_many_iterables(self):
        iterables = [range(1, 10, 2), ["A", "C"], range(15, 7, -2), (5, "d"), "xyz"]
        lengths = [5, 2, 4, 2, 3]
        lprod = list(_lazy_product(iterables, lengths))
        prod = list(product(*iterables))
        self.assertListEqual(lprod, prod)

    def test_laziness(self):

        def range_with_side_effect(n):
            nonlocal side_count
            for i in range(n):
                side_count += 1
                yield i

        side_count = 0
        product(range(2), range_with_side_effect(4))
        self.assertEqual(side_count, 4)
        side_count = 0
        lazy = _lazy_product([range(2), range_with_side_effect(4)], [2, 4])
        self.assertEqual(side_count, 0)
        next(lazy)
        self.assertEqual(side_count, 1)
        next(lazy)
        self.assertEqual(side_count, 2)
        next(lazy)
        self.assertEqual(side_count, 3)
        next(lazy)
        self.assertEqual(side_count, 4)
        next(lazy)
        self.assertEqual(side_count, 4)
        next(lazy)
        self.assertEqual(side_count, 4)
        next(lazy)
        self.assertEqual(side_count, 4)
        next(lazy)
        self.assertEqual(side_count, 4)
        with self.assertRaises(StopIteration):
            next(lazy)


class TestDisambiguator(unittest.TestCase):

    def check_with_tree(self, tree):
        disambiguator = Disambiguator()
        counted_tree = CountTrees().transform(tree)
        collapsed = CollapseAmbiguities().transform(tree)
        regular_disambig = list(disambiguator.visit(tree))
        counted_disambig = list(disambiguator.visit(counted_tree))
        self.assertListEqual(regular_disambig, collapsed)
        self.assertListEqual(counted_disambig, collapsed)

    def test_unambiguous_tree(self):
        tree = Tree("start", ["A", Tree("b", ["B"]), Tree("c", []), "D"])
        self.check_with_tree(tree)

    def test_top_level_ambiguity(self):
        tree = Tree("_ambig", [Tree("start", ["a"]), Tree("start", ["b"])])
        self.check_with_tree(tree)

    def test_lower_lever_ambiguity(self):
        tree = Tree("start", [Tree("_ambig", [Tree("a", []), Tree("b", [])])])
        self.check_with_tree(tree)

    def test_mixed_ambiguity(self):
        tree = Tree("start", [Tree("_ambig", [Tree("a", []), Tree("b", [])]),
                              Tree("_ambig", [Tree("c", []), Tree("d", []), Tree("e", [])]),
                              Tree("h", []),
                              Tree("_ambig", [Tree("f", []), Tree("g", [])])])
        self.check_with_tree(tree)

    def test_nested_ambiguity(self):
        tree = Tree("_ambig", [Tree("s", [Tree("_ambig", [Tree("a", []), Tree("b", []), Tree("c", [])]), "F"]),
                               Tree("s", [Tree("_ambig", [Tree("d", []), Tree("e", [])]), "G"])])
        self.check_with_tree(tree)

    def test_deeply_nested_ambiguity(self):
        nested_tree = Tree("_ambig", [Tree("s", [Tree("_ambig", [Tree("a", []), Tree("b", []), Tree("c", [])]), "F"]),
                               Tree("s", [Tree("_ambig", [Tree("d", []), Tree("e", [])]), "G"])])
        tree = Tree("_ambig", [Tree("start", [Tree("_ambig", [
                Tree("a", [Tree("_ambig", [Tree("_ambig", [Tree("a", []), Tree("b", [])])])]),
                Tree("b", [nested_tree])]),
            ]),
                Tree("start", [Tree("_ambig", [Tree("d", []), Tree("e", [])]), nested_tree])])
        self.check_with_tree(tree)


if __name__ == "__main__":
    unittest.main()
