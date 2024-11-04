import os
import re
import tempfile
from typing import Generator

import pytest

from ..configuration import Configuration
from ..constants import SearchAlgorithm
from ..core.helpers.file_loader import FileLoader


@pytest.fixture
def temp_file() -> Generator[str, None, None]:
    """Fixture to create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"line1\nline2\nline3")
        tmp_path = tmp.name
    yield tmp_path
    os.remove(tmp_path)


@pytest.fixture
def config(temp_file: str) -> Configuration:
    """Fixture to provide a Configuration object."""
    config = Configuration()
    config.FILE_PATH = temp_file
    config.REREAD_ON_QUERY = False
    return config


def test_load_file_data_to_memory_with_os(config: Configuration) -> None:
    """Test loading file data into memory with low-level OS functions."""
    file_loader = FileLoader(config)

    # Load data into memory using low-level search
    loaded_data = file_loader._low_level_search()

    # Verify loaded data
    assert loaded_data[b"line1"], "Expected line1 to be loaded."
    assert loaded_data[b"line2"], "Expected line2 to be loaded."
    assert loaded_data[b"line3"], "Expected line3 to be loaded."
    assert (
        len(loaded_data) == 3
    ), f"Expected 3 lines, found {len(loaded_data)}."


def test_load_file_data_to_memory_open(config: Configuration) -> None:
    """Test loading file data into memory with high-level I/O."""
    file_loader = FileLoader(config)

    # Load data into memory using high-level search
    loaded_data = file_loader._high_level_search()

    # Verify loaded data
    assert loaded_data[b"line1"], "Expected line1 to be loaded."
    assert loaded_data[b"line2"], "Expected line2 to be loaded."
    assert loaded_data[b"line3"], "Expected line3 to be loaded."
    assert (
        len(loaded_data) == 3
    ), f"Expected 3 lines, found {len(loaded_data)}."


def test_search_with_brute_force(config: Configuration) -> None:
    """Test loading file data line-by-line with brute-force search."""
    file_loader = FileLoader(config)

    # Load data into memory using brute-force search
    loaded_data = file_loader._search_with_brute_force()

    # Verify loaded data
    assert loaded_data[b"line1"], "Expected line1 to be loaded."
    assert loaded_data[b"line2"], "Expected line2 to be loaded."
    assert loaded_data[b"line3"], "Expected line3 to be loaded."
    assert (
        len(loaded_data) == 3
    ), f"Expected 3 lines, found {len(loaded_data)}."


def test_search_with_regex(config: Configuration) -> None:
    """Test searching entire file content using regex search."""
    file_loader = FileLoader(config)

    # Perform regex search for an existing pattern
    file_data = file_loader._search_with_regex()
    assert re.search(b"line1", file_data), "Expected line1 to be found."
    assert re.search(b"line2", file_data), "Expected line2 to be found."
    assert re.search(b"line3", file_data), "Expected line3 to be found."


def test_search_with_grep(config: Configuration) -> None:
    """Test searching using the grep command."""
    file_loader = FileLoader(config)

    # Test grep search with an existing pattern
    assert file_loader._search_with_grep(
        b"line1"
    ), "Expected line1 to be found."
    assert file_loader._search_with_grep(
        b"line2"
    ), "Expected line2 to be found."
    assert file_loader._search_with_grep(
        b"line3"
    ), "Expected line3 to be found."


def test_check_text_with_algorithm(config: Configuration) -> None:
    """
    Test checking for existing text in the file using different algorithms.
    """
    file_loader = FileLoader(config)

    # Test with LOW_LEVEL algorithm
    assert file_loader.check_text(
        b"line1", SearchAlgorithm.LOW_LEVEL
    ), "Expected line1 to be found with LOW_LEVEL."

    # Test with HIGH_LEVEL algorithm
    assert file_loader.check_text(
        b"line2", SearchAlgorithm.HIGH_LEVEL
    ), "Expected line2 to be found with HIGH_LEVEL."

    # Test with BRUTE_FORCE algorithm
    assert file_loader.check_text(
        b"line3", SearchAlgorithm.BRUTE_FORCE
    ), "Expected line3 to be found with BRUTE_FORCE."

    # Test with REGEX_SEARCH algorithm
    assert file_loader.check_text(
        b"line1", SearchAlgorithm.REGEX_SEARCH
    ), "Expected line1 to be found with REGEX_SEARCH."

    # Test with GREP_SEARCH algorithm
    assert file_loader.check_text(
        b"line2", SearchAlgorithm.GREP_SEARCH
    ), "Expected line2 to be found with GREP_SEARCH."


def test_check_text_not_exists(config: Configuration) -> None:
    """Test checking for non-existent text in the file."""
    file_loader = FileLoader(config)

    # Test with a non-existent pattern
    assert not file_loader.check_text(
        b"nonexistent", SearchAlgorithm.LOW_LEVEL
    ), "Expected nonexistent pattern to not be found."
    assert not file_loader.check_text(
        b"nonexistent", SearchAlgorithm.HIGH_LEVEL
    ), "Expected nonexistent pattern to not be found."
    assert not file_loader.check_text(
        b"nonexistent", SearchAlgorithm.BRUTE_FORCE
    ), "Expected nonexistent pattern to not be found."
    assert not file_loader.check_text(
        b"nonexistent", SearchAlgorithm.REGEX_SEARCH
    ), "Expected nonexistent pattern to not be found."
    assert not file_loader.check_text(
        b"nonexistent", SearchAlgorithm.GREP_SEARCH
    ), "Expected nonexistent pattern to not be found."


def test_cache_clear(config: Configuration) -> None:
    """Test that clear_file_data_from_memory clears the data cache."""
    file_loader = FileLoader(config)

    # Load data into memory and confirm it's cached
    file_loader._low_level_search()
    assert (
        file_loader._loaded_data
    ), "Expected loaded data to be cached initially."

    # Clear the file data from memory
    file_loader.clear_file_data_from_memory()

    # Check if data is cleared from the memory
    assert not file_loader._loaded_data, (
        "Expected loaded data to be cleared "
        "after calling clear_file_data_from_memory."
    )

    # Verify that load_file_data_to_memory_open reloads after cache clear
    loaded_data_after_clear = file_loader._low_level_search()
    assert (
        loaded_data_after_clear
    ), "Expected data to reload after cache clear."
    assert len(loaded_data_after_clear) == 3, (
        f"Expected 3 lines after reloading, "
        f"found {len(loaded_data_after_clear)}."
    )
