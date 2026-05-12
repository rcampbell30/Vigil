Enhanced Wizard Set Utilities
=============================

This package is a collection of utility functions designed to make everyday
Python development simpler and more expressive.  Originally inspired by a
"wizard set" of handy patterns (like using `max(items, key=rule)`), the
package now includes an expanded suite of functions for working with sequences,
iterables and dictionaries.  It includes wrappers for common built‑ins,
helpers for flattening, grouping, chunking, merging, and more.

Functions are carefully documented and each line of code carries an inline
comment, making the implementation transparent and educational.  The module
was authored by **Rory** — his name appears in the documentation as a
playful note for the user who requested this work, but it is not part of the
package name.

### Installation

The package is a simple folder containing Python files.  Copy the
`wizardset_enhanced` directory into your project or install it as an editable
dependency:

```bash
pip install -e path/to/wizardset_enhanced
```

### Usage

Import directly from the package or from the module.  All functions are
exposed at the package level for convenience:

```python
from wizardset_enhanced import best, flatten, group_by

print(best([1, 2, 3], lambda x: x))  # 3
print(flatten([[1, 2], [3, 4]]))  # [1, 2, 3, 4]
print(group_by(['hi', 'cat', 'dog'], len))  # {2: ['hi'], 3: ['cat', 'dog']}
```

### Available Functions

| Function            | Description |
|---------------------|-------------|
| `best(items, rule)` | Return the item with the highest score according to a rule |
| `worst(items, rule)` | Return the item with the lowest score according to a rule |
| `rank(items, rule, reverse=False)` | Return a sorted list based on a rule |
| `count_where(items, condition)` | Count items satisfying a condition |
| `any_match(items, condition)` | Whether any item satisfies a condition |
| `all_match(items, condition)` | Whether all items satisfy a condition |
| `unique(items)` | Unique items preserving order |
| `frequencies(items)` | Count occurrences of each distinct item |
| `pair(left_items, right_items)` | Pair two iterables into list of tuples |
| `numbered(items, start=0)` | Enumerate items from a starting number |
| `average_score(items, rule)` | Average of scores computed by a rule |
| `explain_best(items, rule)` | Explain the best and second best items |
| `flatten(nested)` | Flatten nested iterables |
| `chunk(items, size)` | Split items into chunks |
| `group_by(items, key)` | Group items by a computed key |
| `duplicates(items)` | List items appearing more than once |
| `transpose(matrix)` | Transpose a matrix |
| `map_values(items, func)` | Apply a function to each item |
| `filter_values(items, condition)` | Filter items by condition |
| `safe_get(mapping, keys, default=None)` | Safely get a nested value |
| `merge(dict_a, dict_b)` | Shallow merge two dicts |
| `nested_merge(dict_a, dict_b)` | Deep merge two dicts |
| `intersection(seq1, seq2)` | Intersection of two sequences |
| `difference(seq1, seq2)` | Items in seq1 not in seq2 |
| `prefix_sum(numbers)` | Cumulative sum of numbers |
| `flatten_dict(d, parent_key='', sep='.')` | Flatten nested dict keys |
| `unflatten_dict(d, sep='.')` | Convert flattened dict to nested |

Each function includes docstrings and comments explaining how it works.  Open
the source code to learn more about the implementation.

Happy coding!