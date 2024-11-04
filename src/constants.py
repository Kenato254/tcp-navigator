from enum import Enum

SearchAlgorithm = Enum(
    'SearchAlgorithm',
    'LOW_LEVEL HIGH_LEVEL BRUTE_FORCE GREP_SEARCH REGEX_SEARCH',
)
"""Enum for file search algorithms.

Attributes:
    LOW_LEVEL: Uses low-level OS functions with memory-mapped I/O.
    HIGH_LEVEL: Uses high-level I/O with memory-mapped access.
    BRUTE_FORCE: Searches line-by-line without full file loading.
    GREP_SEARCH: Searches entire file content using the Linux `grep` command.
    REGEX_SEARCH: Loads file for regex-based search.
"""
