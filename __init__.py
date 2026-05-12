"""
Top level package for the enhanced Wizard Set utilities.

This package exposes all functions from the wizardset module at the package level
for convenience.  Importing from wizardset_enhanced will make the functions
directly available:

    from wizardset_enhanced import best, flatten

The functions themselves are defined in the wizardset module.  See
wizardset_enhanced/wizardset.py for full documentation and line‑by‑line comments.

"""

from .wizardset import (
    any_match,
    all_match,
    average_score,
    best,
    worst,
    rank,
    count_where,
    unique,
    frequencies,
    pair,
    numbered,
    explain_best,
    flatten,
    chunk,
    group_by,
    duplicates,
    transpose,
    map_values,
    filter_values,
    safe_get,
    merge,
    nested_merge,
    intersection,
    difference,
    prefix_sum,
    flatten_dict,
    unflatten_dict,
)

__all__ = [
    'any_match', 'all_match', 'average_score', 'best', 'worst', 'rank', 'count_where',
    'unique', 'frequencies', 'pair', 'numbered', 'explain_best', 'flatten', 'chunk',
    'group_by', 'duplicates', 'transpose', 'map_values', 'filter_values', 'safe_get',
    'merge', 'nested_merge', 'intersection', 'difference', 'prefix_sum',
    'flatten_dict', 'unflatten_dict'
]