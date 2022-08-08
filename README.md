# lark-ambig-tools

`lark-ambig-tools` is a collection of utilities for [lark](https://github.com/lark-parser/lark)'s ambiguous parse
trees[^1].

[^1]: A `Tree` containing `"_ambig"` nodes often produced with the `ambiguity="explicit"` option.

Whether your ambiguous grammar is a bug or a feature, `lark-ambig-tools` helps
you process ambiguity quickly and easily.

## Features:

- Count the total number of derivations in an ambiguous tree
- Lazily iterate over the unambiguous derivations of a tree
- Obtain all unambiguous trees faster and more efficiently than `lark.visitors.CollapseAmbiguities`

## Requirements

- Python 3.6+
- lark 1.0+

**Note**: Only `lark` 1.0+ is officially supported, but `lark-ambig-tools` may
work with older versions.

## Installation

```
pip install lark-ambig-tools
```

Alternatively, include `lark_ambig_tools.py` in your Python project with a copy
of the license.

## Usage

### `CountedTree`

`CountedTree` is a subclass of `lark.Tree` with an additional attribute:
`derivation_count`. `derivation_count` contains the total number of unambiguous trees
that are represented by the tree.

#### Examples

1. Use `CountedTree` during parsing:

```python
from lark import Lark
from lark_ambig_tools import CountedTree

parser = Lark(grammar, ambiguity="explicit", tree_class=CountedTree)
tree = parser.parse(text)
print(tree.derivation_count)
```

2. Transform a `Tree` into a `CountedTree`:

```python
from lark import Lark
from lark_ambig_tools import CountTrees

parser = Lark(grammar, ambiguity="explicit")
tree = parser.parse(text)
counted_tree = CountTrees().transform(tree)
print(counted_tree.derivation_count)
```

**Note**: It is not generally recommended to construct `CountedTree`s directly.

### `Disambiguator`

`Disambiguator` is a `lark.Interpreter` that lazily iterates over the unambiguous
trees represented by an ambiguous tree. It is a faster and more memory-efficient
alternative to lark's `CollapseAmbiguities`. By providing trees in the
same order trees as `CollapseAmbiguities`, `Disambiguator` is a drop-in replacement.

#### Example

```python
from lark import Lark
from lark_ambig_tools import Disambiguator

parser = Lark(grammar, ambiguity="explicit")
ambig_tree = parser.parse(text)

disambiguator = Disambiguator()
for tree in disambiguator.visit(ambig_tree):
    # process unambiguous tree
    ...
```

#### Extra Lazy `Disambiguator`

When an instance of `CountedTree` is passed to `Disambiguator.visit`,
`Disambiguator` takes advantage the known derivation counts to be even more
lazy -- reducing computation and memory usage. Using  `Disambiguator` with
`CountedTree` is ideal when you do not need to iterate over all the trees. i.e.
You stop iterating when you find one tree that meets your requirements.
If you always need all the trees, most of the time it is better to pass a regular
`Tree`.

For more insights into how to best use `Disambiguator`, see the [benchmarks](#benchmarks).

## Benchmarks

### Overview

`benchmark.py` contains benchmarks to test the performance of `Disambiguator`
(with both `Tree` and `CountedTree`) and `CollapseAmbiguities`.

#### Tasks

The benchmarks cover two different use cases with the following tests:

- Getting the first unambiguous tree
- Getting all unambiguous trees

#### Trees

Each task is run with three different types of ambiguous trees:

- A small tree that is neither deep nor of high degree (4 derivations)
- A deep tree that is deep and of low degree (64 derivations)
- A wide tree that is not deep and of a high degree (216 derivations)

### Running

1. Install the requirements:

```
pip install lark_ambig_tools[benchmark]
```

2. Run the benchmarks:

```
pytest benchmark.py
```

### Results

The following table summarizes some of the key metrics from one run of the
benchmarks.


| Name (time in us)                        |         Min         |          Max          |       Mean          |   StdDev          |     Median          |
| -----------------------------------------|---------------------|-----------------------|---------------------|-------------------|---------------------|
| test_disambiguator_counted_first[small]  |     13.6640 (1.0)   |      52.6320 (1.04)   |    14.2129 (1.0)    |   1.5089 (1.37)   |    14.0090 (1.0)    |
| test_disambiguator_first[small]          |     15.5660 (1.14)  |      50.6990 (1.0)    |    16.1473 (1.14)   |   1.6425 (1.49)   |    15.9220 (1.14)   |
| test_disambiguator_counted_first[wide]   |     21.0970 (1.54)  |      56.4830 (1.11)   |    21.7083 (1.53)   |   1.9241 (1.75)   |    21.4750 (1.53)   |
| test_disambiguator_all[small]            |     28.4980 (2.09)  |      90.8440 (1.79)   |    29.1030 (2.05)   |   1.1015 (1.0)    |    28.9740 (2.07)   |
| test_disambiguator_counted_all[small]    |     32.6300 (2.39)  |      95.0600 (1.87)   |    33.6988 (2.37)   |   2.9152 (2.65)   |    33.2920 (2.38)   |
| test_collapse_ambiguities_all[small]     |     39.0030 (2.85)  |      97.3070 (1.92)   |    40.0052 (2.81)   |   2.9053 (2.64)   |    39.6080 (2.83)   |
| test_disambiguator_counted_first[deep]   |     46.9520 (3.44)  |     120.7470 (2.38)   |    48.3013 (3.40)   |   4.5244 (4.11)   |    47.6360 (3.40)   |
| test_disambiguator_first[wide]           |     83.5920 (6.12)  |     207.2310 (4.09)   |    86.4240 (6.08)   |   7.1662 (6.51)   |    85.4380 (6.10)   |
| test_disambiguator_first[deep]           |    330.8410 (24.21) |  11,565.8670 (228.13) |   342.4290 (24.09)  | 236.3552 (214.58) |   334.1530 (23.85)  |
| test_disambiguator_counted_all[wide]     |    440.9970 (32.27) |   1,000.8610 (19.74)  |   448.8748 (31.58)  |  25.9656 (23.57)  |   444.5130 (31.73)  |
| test_disambiguator_all[wide]             |    643.2160 (47.07) |  11,475.9880 (226.36) |   728.5492 (51.26)  | 840.6795 (763.25) |   650.9210 (46.46)  |
| test_disambiguator_all[deep]             |    716.1010 (52.41) |  12,895.9900 (254.36) |   831.8742 (58.53)  | 966.1033 (877.12) |   739.4460 (52.78)  |
| test_collapse_ambiguities_all[deep]      |    924.8430 (67.68) |  12,040.0150 (237.48) | 1,019.8753 (71.76)  | 932.9566 (847.02) |   931.7700 (66.51)  |
| test_collapse_ambiguities_all[wide]      |  1,008.2290 (73.79) |  12,064.4850 (237.96) | 1,104.9380 (77.74)  | 910.6654 (826.78) | 1,016.4430 (72.56)  |
| test_disambiguator_counted_all[deep]     |  1,014.4010 (74.24) |  12,216.7780 (240.97) | 1,118.3364 (78.68)  | 952.4029 (864.68) | 1,022.4965 (72.99)  |


**Note**: Getting the first tree from `CollapseAmbiguities` is the same as
getting all the trees.

#### Insights

The following insights may be gathered from the above results:

- `Disambiguator` with `CountedTree` is the fastest way to get the first tree.
- `Disambiguator` with `Tree` beats `CollapseAmbiguities` in getting all trees for any tree type.
- Deep ambiguous trees tend to require more computation than wide trees even when they have fewer total derivations.

#### Limitations

Of course, the performance of the different classes may vary depending on the
hardware, environment, and workload. Furthermore, these benchmarks only test
the runtime of the code. They do not take into account other relevant
characteristics such as memory usage and performance with varying frequencies of requests.

However, hopefully these results offer a helpful starting point for using
`Disambiguator`.

## Testing

Run the tests with

```
python test_lark_ambig_tools.py
```

or with tox:

```
tox
```

## License

This project is under the [MIT](LICENSE) license.
