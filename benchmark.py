from lark import Tree
from lark.visitors import CollapseAmbiguities

import pytest

from lark_ambig_tools import CountTrees, Disambiguator


@pytest.fixture(params=[(2, 2), (6, 2), (2, 6)], ids=["small", "deep", "wide"])
def ambig_tree(request):

    data = "abcdefghijklmnopqrstuvwxyz"

    def create_tree(depth, ambig):
        if depth == 0:
            return "A"
        if ambig:
            tree = Tree("_ambig", [])
        else:
            tree = Tree(data[depth], [])
        for i in range(degree):
            tree.children.append(Tree(data[i], []))
        for t in tree.children:
            for i in range(degree // 2):
                if i % 2 == 0:
                    t.children.append(create_tree(depth - 1, ambig=True))
                else:
                    t.children.append(create_tree(depth - 1, ambig=False))
        return tree

    depth_factor = request.param[0]
    degree = request.param[1]
    return create_tree(depth_factor, ambig=True)


def get_all(tree, disambiguator):
    list(disambiguator.visit(tree))


def test_disambiguator_all(ambig_tree, benchmark):
    benchmark(get_all, ambig_tree, Disambiguator())


def test_disambiguator_counted_all(ambig_tree, benchmark):
    counted_tree = CountTrees().transform(ambig_tree)
    benchmark(get_all, counted_tree, Disambiguator())


def test_collapse_ambiguities_all(ambig_tree, benchmark):
    collapser = CollapseAmbiguities()
    benchmark(collapser.transform, ambig_tree)


def get_first(tree, disambiguator):
    next(disambiguator.visit(tree))


def test_disambiguator_first(ambig_tree, benchmark):
    benchmark(get_first, ambig_tree, Disambiguator())


def test_disambiguator_counted_first(ambig_tree, benchmark):
    counted_tree = CountTrees().transform(ambig_tree)
    benchmark(get_first, counted_tree, Disambiguator())
