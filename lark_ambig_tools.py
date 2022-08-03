import sys
from functools import reduce
from itertools import chain, product, repeat
from typing import Any, Collection, Iterable, Iterator, Tuple, TypeVar

from lark import Tree, Transformer
from lark.visitors import Interpreter

if sys.version_info >= (3, 8):
    from math import prod
else:

    def prod(nums, start=1):
        return reduce(lambda x, y: x * y, nums, start)


T = TypeVar("T")


class CountedTree(Tree):
    def __init__(self, data, children, meta=None):
        super().__init__(data, children, meta)
        derivation_counts = map(_get_derivation_count, children)
        self.derivation_count = (sum(derivation_counts) if data == "_ambig" else prod(derivation_counts))


class CountTrees(Transformer):
    def __default__(self, data, children, meta):
        return CountedTree(data, children, meta)


def _get_derivation_count(tree: Any) -> int:
    return getattr(tree, "derivation_count", 1)


def _repeat_each(iterable: Iterable[T], n: int) -> Iterator[T]:
    return chain.from_iterable(map(repeat, iterable, repeat(n)))


def _ncycles(iterable: Iterable[T], n: int) -> Iterator[T]:
    if n > 0:
        saved = []
        for element in iterable:
            yield element
            saved.append(element)
        yield from chain.from_iterable(repeat(saved, n - 1))


def _lazy_product(iterables: Collection[Iterable[T]], lengths: Collection[int]) -> Iterator[Tuple[T, ...]]:
    cycle_count = 1
    repeat_count = prod(lengths)
    iterators = []
    for iterable, length in zip(iterables, lengths):
        repeat_count //= length
        iterators.append(_ncycles(_repeat_each(iterable, repeat_count), cycle_count))
        cycle_count *= length
    return zip(*iterators)


class Disambiguator(Interpreter):
    def _ambig(self, tree: Tree) -> Iterator[Tree]:
        for child in tree.children:
            yield from self.visit(child)

    def __default__(self, tree: Tree) -> Iterator[Tree]:
        if isinstance(tree, CountedTree) and tree.derivation_count == 1:
            yield tree
        else:
            yield from self._generate_subtrees(tree)

    def _generate_subtrees(self, tree: Tree) -> Iterator[Tree]:
        sub_tree_iterators = [self.visit(child) if isinstance(child, Tree) else (child,) for child in tree.children]
        if isinstance(tree, CountedTree):
            derivation_counts = [_get_derivation_count(child) for child in tree.children]
            children_lists = _lazy_product(sub_tree_iterators, derivation_counts)
        else:
            children_lists = product(*sub_tree_iterators)
        for children_list in children_lists:
            yield Tree(tree.data, list(children_list))
