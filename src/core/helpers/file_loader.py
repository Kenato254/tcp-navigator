import mmap
import os
import re
import subprocess
import sys
from collections import defaultdict
from contextlib import closing
from functools import lru_cache

from ...configuration import Configuration
from ...constants import SearchAlgorithm
from .logging_helper import LoggingDescriptor


class FileLoader:
    """
    FileLoader class responsible for loading file data into memory and
    providing an interface to query data within the file.

    Attributes:
        __logger (LoggingDescriptor): Logger instance for logging events.
        file_path (str): Path of the file to load.
        _reread_on_query (bool): Determines if the file should be re-read
            for each query.
        _loaded_data (defaultdict[bytes, bool]): Cache storing loaded file
        lines as keys with True values, representing presence.
    """

    __logger = LoggingDescriptor("FileLoader")

    def __init__(self, config: Configuration) -> None:
        """Initializes file path and read behavior from configuration.

        Args:
            config (Configuration): Holds settings for file path and query
                behavior.

        Raises:
            AttributeError: Logs error if configuration properties are missing.
        """
        try:
            self.file_path: str = config.FILE_PATH
            self._reread_on_query: bool = config.REREAD_ON_QUERY
        except AttributeError as err:
            self.__logger.error(
                f"Setting instance attributes failed with: {err}"
            )
        self._loaded_data: defaultdict[bytes, bool] = defaultdict(
            lambda: False, {}
        )

    @lru_cache(maxsize=None)
    def _low_level_search(self) -> defaultdict[bytes, bool]:
        """Efficiently loads file data into memory using low-level OS
        functions.

        This method utilizes `os.open` and `os.fdopen` for file access,
        combined with memory-mapped I/O (`mmap`) for high-performance
        reading. File lines are cached in memory for fast subsequent access,
        with each line ending stripped of `\r`.

        Returns:
            defaultdict[bytes, bool]: A dictionary-like cache of file lines
            with line presence indicated as True for rapid lookups.

        Raises:
            OSError: Exits if an error occurs while reading or mapping
                the file.
        """
        try:
            # Open the file descriptor with a context manager
            with os.fdopen(
                os.open(self.file_path, os.O_RDONLY), 'rb'
            ) as file:
                # Memory-map the file content with `closing` to ensure cleanup
                with closing(
                    mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
                ) as buffer:
                    # Read the entire file into memory
                    self._loaded_data.update(
                        {
                            pattern.rstrip(b"\r"): True
                            for pattern in buffer[:].split(b"\n")
                        }
                    )

        except OSError as e:
            self.__logger.error(f"Error reading the file: {e}")
            sys.exit(-1)

        return self._loaded_data

    def _high_level_search(self) -> defaultdict[bytes, bool]:
        """Loads file data into memory using Python's `open` function.

        This method opens the file directly with `open`, then uses
        memory-mapped I/O (`mmap`) for efficient data loading into memory.
        The file lines are cached with each entry marked True to
        indicate line presence, allowing for quick access.

        Returns:
            defaultdict[bytes, bool]: Cached file lines as keys with
            True values, facilitating fast checks for each line.

        Raises:
            OSError: Exits if an error occurs while accessing or mapping
                the file.
        """
        try:
            # Open the file descriptor with a context manager
            with open(self.file_path, 'rb') as file:
                # Memory-map the file content with `closing` to ensure cleanup
                with closing(
                    mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
                ) as buffer:
                    # Read the entire file into memory
                    self._loaded_data.update(
                        {
                            pattern.rstrip(b"\r"): True
                            for pattern in buffer[:].split(b"\n")
                        }
                    )

        except OSError as e:
            self.__logger.error(f"Error reading the file: {e}")
            sys.exit(-1)

        return self._loaded_data

    def _search_with_brute_force(self) -> defaultdict[bytes, bool]:
        """
        Loads file data line-by-line into memory using buffered I/O.

        This method opens the file and reads it line-by-line, storing each
        line as a key in a dictionary for fast in-memory lookup.

        Returns:
            defaultdict[bytes, bool]: Cached file lines as keys with
                True values.

        Raises:
            OSError: Exits if an error occurs while accessing the file.
        """
        try:
            # Use buffered I/O to read the file
            with open(self.file_path, 'rb') as file:
                for line in file:
                    # Store each line in the cache dictionary with
                    #  `True` as value
                    self._loaded_data[line.rstrip(b"\r\n")] = True

        except OSError as e:
            self.__logger.error(f"Error reading the file: {e}")
            sys.exit(-1)

        return self._loaded_data

    def _search_with_regex(self) -> bytes:
        """Loads the entire file data into memory as a single byte string.

        This method reads the entire file, caching it for regex-based searches.

        Returns:
            bytes: The entire file content in bytes.

        Raises:
            OSError: Raise if an error occurs while reading the file.
        """
        try:
            self.__logger.info(
                f"Loading file '{self.file_path}' for regex search"
            )

            with open(self.file_path, 'rb') as file:
                # Read the entire file into a byte string
                file_data = file.read()

        except OSError as e:
            self.__logger.error(f"Error reading the file: {e}")

        return file_data

    def _search_with_grep(self, pattern: bytes) -> bool:
        """Searches for a given byte pattern in the file using
        the Linux `grep` command.

        Args:
            pattern (bytes): The byte pattern to search for in the file.

        Returns:
            bool: True if the pattern is found, False otherwise.

        Raises:
            Exception: Logs any error that occurs during file
                reading or search.
        """
        try:
            result = subprocess.run(
                ['grep', '-q', pattern, self.file_path],
                capture_output=True,
            )
            found = result.returncode == 0
        except Exception as e:
            self.__logger.error(f"Error reading the file: {e}")
            found = False
        return found

    def check_text(
        self,
        pattern: bytes,
        algorithm: SearchAlgorithm = SearchAlgorithm.GREP_SEARCH,
    ) -> bool:
        """Checks if the specified pattern exists in the file using t
        he selected search algorithm.

        Args:
            pattern (bytes): The byte pattern to search for within the file.
            algorithm (SearchAlgorithm): The search algorithm to apply.
            Options are:
            - SearchAlgorithm.LOW_LEVEL:
                Uses low-level OS functions for memory-mapped search.

            - SearchAlgorithm.HIGH_LEVEL:
                Uses high-level I/O for memory-mapped search.

            - SearchAlgorithm.BRUTE_FORCE:
                Reads and searches the file line by line.

            - SearchAlgorithm.GREP_SEARCH:
                Searches entire file content using the Linux `grep` command.

            - SearchAlgorithm.REGEX_SEARCH:
                Searches entire file content using regex.

        Returns:
            bool: True if the pattern is found in the file, False otherwise.

        Raises:
            OSError: If an error occurs during file access or reading,
                with logging for details.
        """

        # Clear caches if re-reading is requested on each query
        if self._reread_on_query:
            self.clear_file_data_from_memory()

        # Select the appropriate search method based on the algorithm
        try:
            self.__logger.info(f"Current search algorithm : {algorithm}")
            match algorithm:
                case SearchAlgorithm.LOW_LEVEL:
                    return self._low_level_search()[pattern]

                case SearchAlgorithm.HIGH_LEVEL:
                    return self._high_level_search()[pattern]

                case SearchAlgorithm.BRUTE_FORCE:
                    return self._search_with_brute_force()[pattern]

                case SearchAlgorithm.GREP_SEARCH:
                    return self._search_with_grep(pattern)

                case SearchAlgorithm.REGEX_SEARCH:
                    file_data = self._search_with_regex()

                    # Compile the regex pattern for better performance
                    # on repeated searches
                    compiled_pattern = re.compile(pattern)

                    # Search for the pattern in the file content
                    return bool(compiled_pattern.search(file_data))

        except OSError as e:
            self.__logger.error(f"Error reading the file: {e}")
            raise

    def clear_file_data_from_memory(self) -> None:
        """
        Clears all file data from memory.
        """
        if self._loaded_data:
            self._loaded_data.clear()

            self._low_level_search.cache_clear()
