"""
wizardset.py - A collection of utility functions to make common tasks in Python
easier, inspired by a set of so‑called "wizard" patterns.  Each function is
written with clarity in mind and fully commented so that developers at all
levels can understand how they work under the hood.

The module collects a number of helpers that operate on sequences, iterables
and dictionaries.  These helpers wrap around Python’s built‑in functions or
provide simple algorithms for tasks like flattening lists, grouping items,
finding duplicates and more.  Many of the functions accept a `rule` or
`condition` argument so you can customise how items are compared or
selected.

Author: Rory (not part of the package name, but acknowledged here in the
documentation as per the user's request).
"""

from collections import Counter
from typing import Any, Callable, Dict, Iterable, Iterator, List, Sequence, Tuple, TypeVar

T = TypeVar('T')  # Generic type variable for items in sequences
K = TypeVar('K')  # Generic type variable for keys


def best(items: Sequence[T], rule: Callable[[T], Any]) -> T:
    """Return the item with the highest score according to a provided rule.

    This function is a wrapper around Python's built‑in max() function, but
    requires a rule (key function) to score each item.  We deliberately
    avoid a default rule so that callers must think about what makes an
    item "best" in their context.

    :param items: A non‑empty sequence of items to evaluate.
    :param rule: A function that takes an item and returns a value used for comparison.
    :return: The item with the highest score.
    """
    # Use max() with the provided rule as the key function.  The key function
    # computes a value for each item which max() then compares to find the
    # highest.  The item itself is returned, not the computed value.
    return max(items, key=rule)


def worst(items: Sequence[T], rule: Callable[[T], Any]) -> T:
    """Return the item with the lowest score according to a provided rule.

    Similar to best(), but uses min() to find the item with the smallest
    computed value.  Requires a rule so that the caller explicitly defines
    how items are compared.

    :param items: A non‑empty sequence of items to evaluate.
    :param rule: A function that takes an item and returns a value used for comparison.
    :return: The item with the lowest score.
    """
    # Use min() with the provided rule as the key function.  The key function
    # computes a value for each item which min() then compares to find the
    # smallest.  The item itself is returned, not the computed value.
    return min(items, key=rule)


def rank(items: Sequence[T], rule: Callable[[T], Any], reverse: bool = False) -> List[T]:
    """Return a new list of items sorted by a rule.

    The rule determines the value to sort by.  The reverse flag controls
    ascending vs. descending order.  A new list is returned so that the
    original sequence remains unchanged.

    :param items: A sequence of items to sort.
    :param rule: A function that computes a sortable value for each item.
    :param reverse: If True, sort in descending order.  Defaults to False.
    :return: A list of items sorted by the computed key.
    """
    # Use Python's built‑in sorted() with the key and reverse arguments.
    # sorted() always returns a new list, leaving the original sequence untouched.
    return sorted(items, key=rule, reverse=reverse)


def count_where(items: Iterable[T], condition: Callable[[T], bool]) -> int:
    """Count how many items in an iterable satisfy a condition.

    The condition function should return True for items that should be counted.
    The sum() built‑in counts the number of True values by leveraging the fact
    that True evaluates to 1 and False to 0 in arithmetic operations.

    :param items: An iterable of items to test.
    :param condition: A function returning True for items that should be counted.
    :return: The number of items satisfying the condition.
    """
    # Generate a sequence of True/False results for each item and sum them.
    # Each True counts as 1 and each False as 0, so the sum is the count.
    return sum(1 for item in items if condition(item))


def any_match(items: Iterable[T], condition: Callable[[T], bool]) -> bool:
    """Return True if any item in the iterable satisfies the condition.

    Uses Python's built‑in any() to short‑circuit and return True upon the
    first True result from the condition.  Returns False if no items satisfy
    the condition.

    :param items: An iterable of items to test.
    :param condition: A function returning True for matching items.
    :return: True if at least one item matches, otherwise False.
    """
    # Use a generator expression inside any() to evaluate each item lazily.
    return any(condition(item) for item in items)


def all_match(items: Iterable[T], condition: Callable[[T], bool]) -> bool:
    """Return True if all items in the iterable satisfy the condition.

    Uses Python's built‑in all() to check that every item returns True for
    the condition.  Returns False as soon as a False result is encountered.

    :param items: An iterable of items to test.
    :param condition: A function returning True for matching items.
    :return: True if all items match, otherwise False.
    """
    # Use a generator expression inside all() to evaluate each item lazily.
    return all(condition(item) for item in items)


def unique(items: Iterable[T]) -> List[T]:
    """Return a list of unique items, preserving order of first appearance.

    Uses a set to track which items have already been seen.  As soon as an
    item appears for the first time it is added to the result and to the
    seen set.  Subsequent duplicates are ignored.  Order is maintained as
    items are appended to the result list in the order they are first seen.

    :param items: An iterable that may contain duplicates.
    :return: A list of unique items in their first‑occurrence order.
    """
    seen = set()  # Keep track of items that have already been encountered
    result: List[T] = []  # List to store the unique items in order
    for item in items:
        if item not in seen:
            # If we haven't seen this item before, add it to both the set
            # and the result list.
            seen.add(item)
            result.append(item)
    return result


def frequencies(items: Iterable[T]) -> Counter:
    """Count how many times each distinct item appears.

    Returns a Counter object from the collections module which is a
    subclass of dict mapping each distinct item to its count.

    :param items: An iterable of hashable items.
    :return: A Counter mapping items to their frequencies.
    """
    # The Counter constructor consumes the iterable and tallies counts.
    return Counter(items)


def pair(left_items: Iterable[T], right_items: Iterable[K]) -> List[Tuple[T, K]]:
    """Pair two iterables together into a list of tuples.

    The pairing stops when the shorter iterable is exhausted.

    :param left_items: First iterable of items.
    :param right_items: Second iterable of items.
    :return: A list of (left_item, right_item) tuples.
    """
    # Use Python's built‑in zip() to pair elements.  Convert the zip object
    # (an iterator) to a list so that the result is a list of tuples.
    return list(zip(left_items, right_items))


def numbered(items: Iterable[T], start: int = 0) -> List[Tuple[int, T]]:
    """Return items paired with incremental numbers starting from a given value.

    This is a wrapper around enumerate() that returns a list of tuples.  It
    is often more convenient to work with enumerated items as a list rather
    than an iterator when debugging or printing.

    :param items: An iterable of items to enumerate.
    :param start: The starting number for enumeration.  Defaults to 0.
    :return: A list of (index, item) tuples.
    """
    # Python's enumerate() yields pairs of (index, item).  We convert the
    # enumerate object to a list for immediate consumption.
    return list(enumerate(items, start=start))


def average_score(items: Iterable[T], rule: Callable[[T], float]) -> float:
    """Return the average score of all items based on a rule.

    Computes the rule for each item, sums the scores and divides by the
    number of items.  Raises ValueError if no items are provided to avoid
    division by zero.

    :param items: An iterable of items to score.
    :param rule: A function that computes a numeric score for each item.
    :return: The average of the computed scores.
    :raises ValueError: If the iterable is empty.
    """
    # Convert to a list so we can iterate twice (for sum and for len)
    item_list = list(items)
    if not item_list:
        # It's an error to compute an average of zero items, so raise.
        raise ValueError("Cannot compute average of empty iterable")
    # Compute all scores in a separate list comprehension.  This makes the
    # code easier to read and avoids recomputing the score twice.
    scores = [rule(item) for item in item_list]
    # Sum all scores and divide by the number of scores to get the mean.
    return sum(scores) / len(scores)


def explain_best(items: Sequence[T], rule: Callable[[T], float]) -> Dict[str, Any]:
    """Return the best item, its score, second best item and the gap between them.

    This function sorts the items by the rule, then extracts the top two
    items.  It computes each of their scores and the difference.  The
    information is returned in a dict for clarity.

    :param items: A sequence of items to evaluate.
    :param rule: A function that computes a numeric score for each item.
    :return: A dict with keys 'best', 'best_score', 'second', 'second_score', 'gap'.
    :raises ValueError: If fewer than two items are provided.
    """
    if len(items) < 2:
        # We need at least two items to compare best and second best.
        raise ValueError("Need at least two items to explain best and second best")
    # Sort items descending by score; result is a new list.
    ranked_items = sorted(items, key=rule, reverse=True)
    best_item = ranked_items[0]  # The top item
    second_item = ranked_items[1]  # The runner‑up
    best_score = rule(best_item)  # Compute its score
    second_score = rule(second_item)  # Compute second score
    gap = best_score - second_score  # Difference between scores
    # Return a dictionary summarising the comparison
    return {
        "best": best_item,
        "best_score": best_score,
        "second": second_item,
        "second_score": second_score,
        "gap": gap,
    }


# -----------------------------------------------------------------------------
# Additional helper functions for everyday development
#
# The following functions go beyond the original wizard set.  They aim to
# support common patterns like flattening nested iterables, grouping items by a
# key, finding duplicates, computing differences, and more.  Each function
# includes inline comments to explain its workings.
# -----------------------------------------------------------------------------

def flatten(nested: Iterable[Iterable[T]]) -> List[T]:
    """Flatten a nested iterable (e.g., list of lists) into a single list.

    For example:
        flatten([[1, 2], [3, 4]]) -> [1, 2, 3, 4]

    :param nested: An iterable containing sub‑iterables.
    :return: A flat list containing all elements from the sub‑iterables.
    """
    result: List[T] = []  # Prepare an empty list for collecting results
    for sub in nested:
        # Each sub is itself an iterable; extend the result with its items
        for item in sub:
            result.append(item)
    return result


def chunk(items: Sequence[T], size: int) -> List[List[T]]:
    """Split a sequence into chunks of a given size.

    The last chunk may be smaller if there are not enough items.

    :param items: A sequence to divide into chunks.
    :param size: The size of each chunk; must be positive.
    :return: A list of lists, each containing up to `size` items.
    :raises ValueError: If size is not positive.
    """
    if size <= 0:
        # Disallow non‑positive chunk sizes
        raise ValueError("Chunk size must be a positive integer")
    result: List[List[T]] = []  # Prepare list to hold chunks
    # Iterate over indices from 0 to length in steps of size
    for i in range(0, len(items), size):
        # Slice a chunk from the sequence and append it
        result.append(list(items[i:i + size]))
    return result


def group_by(items: Iterable[T], key: Callable[[T], K]) -> Dict[K, List[T]]:
    """Group items into a dictionary keyed by the result of a key function.

    For example, group words by their length:
        group_by(["cat", "dog", "elephant"], len) -> {3: ["cat", "dog"], 8: ["elephant"]}

    :param items: An iterable of items to group.
    :param key: A function that produces a key for each item.
    :return: A dictionary mapping each key to a list of items producing that key.
    """
    result: Dict[K, List[T]] = {}  # Prepare an empty dict for groups
    for item in items:
        k = key(item)  # Compute the key for this item
        # Use setdefault() to initialise a list for this key if needed
        result.setdefault(k, []).append(item)
    return result


def duplicates(items: Iterable[T]) -> List[T]:
    """Return a list of items that appear more than once in the iterable.

    The result contains each duplicate item only once, in the order of
    first duplication.  Uses a set to track seen items and another set
    to track which items have been added to the duplicates list.

    :param items: An iterable of hashable items.
    :return: A list of items that occurred multiple times.
    """
    seen = set()  # Items seen at least once
    added = set()  # Duplicate items already added to the result
    result: List[T] = []  # List to hold duplicate items
    for item in items:
        if item in seen:
            if item not in added:
                # This is the first time we've spotted this duplicate
                result.append(item)
                added.add(item)
        else:
            # First time seeing this item
            seen.add(item)
    return result


def transpose(matrix: Sequence[Sequence[T]]) -> List[List[T]]:
    """Transpose a 2D matrix represented as a sequence of sequences.

    Converts rows to columns and columns to rows.  All rows should be the
    same length; if they are not, extra values will be ignored where rows
    are shorter.

    :param matrix: A sequence of sequences representing the matrix rows.
    :return: A new matrix with rows and columns swapped.
    """
    # zip(*matrix) pairs together the i‑th elements of each row.  We wrap in
    # map(list, ...) to convert each tuple into a list.  The list() outer
    # call collects all rows into a list.
    return [list(row) for row in zip(*matrix)]


def map_values(items: Iterable[T], func: Callable[[T], K]) -> List[K]:
    """Apply a function to each item and return a list of results.

    This is equivalent to the built‑in map(), but returns a list directly
    which can be more convenient for immediate use or printing.

    :param items: An iterable of items to transform.
    :param func: A function to apply to each item.
    :return: A list of transformed items.
    """
    # Use a list comprehension to apply func to each item
    return [func(item) for item in items]


def filter_values(items: Iterable[T], condition: Callable[[T], bool]) -> List[T]:
    """Return a list of items that satisfy a condition.

    Equivalent to the built‑in filter(), but returns a list directly.

    :param items: An iterable of items to test.
    :param condition: A function returning True for items to keep.
    :return: A list of items where condition(item) is True.
    """
    # Use a list comprehension to select items where condition(item) is True
    return [item for item in items if condition(item)]


def safe_get(mapping: Dict[str, Any], keys: Sequence[str], default: Any = None) -> Any:
    """Safely retrieve a nested value from a dictionary using a sequence of keys.

    If any key along the path is missing, returns the default value instead
    of raising a KeyError.  Useful when dealing with deeply nested JSON.

    :param mapping: The dictionary to search.
    :param keys: A sequence of keys defining the path to the desired value.
    :param default: The value to return if the path is missing.  Defaults to None.
    :return: The nested value or the default.
    """
    current: Any = mapping  # Start at the top level
    for key in keys:
        # If current is a dict and has the key, dive deeper
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            # Missing key: return the default value immediately
            return default
    return current


def merge(dict_a: Dict[str, Any], dict_b: Dict[str, Any]) -> Dict[str, Any]:
    """Shallow merge two dictionaries, with values from dict_b overriding dict_a.

    The returned dictionary contains keys from both inputs.  If the same key
    appears in both dictionaries, the value from dict_b is used.

    :param dict_a: The first dictionary.
    :param dict_b: The second dictionary whose values override dict_a.
    :return: A new dictionary containing all keys from both inputs.
    """
    # Start with a copy of dict_a so we don't mutate the original
    result = dict_a.copy()
    # Update the result with dict_b.  Existing keys are overridden.
    result.update(dict_b)
    return result


def nested_merge(dict_a: Dict[str, Any], dict_b: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries.

    For any keys that map to dictionaries in both inputs, nested_merge is
    called on the sub‑dictionaries.  Non‑dict values in dict_b override
    values from dict_a.

    :param dict_a: The first dictionary.
    :param dict_b: The second dictionary whose values override or extend dict_a.
    :return: A new dictionary representing the deep merge.
    """
    result: Dict[str, Any] = dict_a.copy()  # Copy dict_a to avoid mutation
    for key, value in dict_b.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # If both values are dicts, merge them recursively
            result[key] = nested_merge(result[key], value)
        else:
            # Otherwise override or add the value from dict_b
            result[key] = value
    return result


def intersection(seq1: Iterable[T], seq2: Iterable[T]) -> List[T]:
    """Return the intersection of two sequences as a list.

    Items appear in the result in the order they appear in seq1.  Only items
    that are present in both sequences are included.  Uses a set for O(1)
    membership tests on seq2.

    :param seq1: The first sequence.
    :param seq2: The second sequence.
    :return: A list of items that are in both seq1 and seq2.
    """
    set2 = set(seq2)  # Convert seq2 to a set for fast lookup
    result: List[T] = []  # List to collect intersection items
    for item in seq1:
        if item in set2:
            result.append(item)
    return result


def difference(seq1: Iterable[T], seq2: Iterable[T]) -> List[T]:
    """Return the items in seq1 that are not in seq2.

    Items retain the order in which they appear in seq1.  Uses a set of
    seq2 for efficient membership testing.

    :param seq1: The sequence to subtract from.
    :param seq2: The sequence whose items should be removed.
    :return: A list of items in seq1 that are not in seq2.
    """
    set2 = set(seq2)  # Convert seq2 to a set for fast membership tests
    result: List[T] = []  # Prepare list to collect differences
    for item in seq1:
        if item not in set2:
            result.append(item)
    return result


def prefix_sum(numbers: Iterable[float]) -> List[float]:
    """Compute the cumulative sum (prefix sum) of a sequence of numbers.

    For example:
        prefix_sum([1, 2, 3]) -> [1, 3, 6]

    :param numbers: An iterable of numbers (ints or floats).
    :return: A list of the same length where each element is the sum of all
             preceding numbers including the current one.
    """
    total = 0.0  # Running total
    result: List[float] = []  # List to collect prefix sums
    for number in numbers:
        total += number  # Add the current number to the running total
        result.append(total)  # Append the new total
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary, joining keys with a separator.

    For example:
        {'a': {'b': 1, 'c': 2}, 'd': 3} -> {'a.b': 1, 'a.c': 2, 'd': 3}

    :param d: The dictionary to flatten.
    :param parent_key: The base key to prepend to nested keys.  Used in recursion.
    :param sep: The separator between nested key parts.  Default is '.'.
    :return: A new dictionary with flattened keys.
    """
    items: List[Tuple[str, Any]] = []  # List to collect flattened key-value pairs
    for k, v in d.items():
        # Construct the new key by joining parent_key and current key
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            # Recurse into nested dicts
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            # Add the simple key-value pair
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """Convert a flattened dictionary back to a nested dictionary.

    This is the inverse of flatten_dict().  Keys containing separators are
    split into parts to create nested dictionaries.

    :param d: The flattened dictionary to expand.
    :param sep: The separator used in flattened keys.  Default is '.'.
    :return: A new nested dictionary.
    """
    result: Dict[str, Any] = {}  # Prepare an empty dictionary
    for compound_key, value in d.items():
        keys = compound_key.split(sep)  # Split the compound key into parts
        current = result  # Start at the top level of the result dict
        for part in keys[:-1]:
            # For each intermediate part, create a dict if missing
            current = current.setdefault(part, {})
        # Set the value at the deepest level
        current[keys[-1]] = value
    return result


# End of wizardset.py