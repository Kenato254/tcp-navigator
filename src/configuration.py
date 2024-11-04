from __future__ import annotations

import sys
from configparser import ConfigParser, NoOptionError, NoSectionError
from pathlib import Path

from .core.helpers.logging_helper import LoggingDescriptor


class Configuration:
    """Configuration class that reads settings from a config file.

    Attributes:
        __logger (LoggingDescriptor): Logger for the Configuration class.
        _config (ConfigParser): The configuration parser instance.
        _CONFIG_PATH (Path): The path to the configuration file.
        HOST (str): The server host address.
        PORT (int): The server port number.
        REREAD_ON_QUERY (bool): Indicates whether to re-read the file on query.
        FILE_PATH (str): The file path for the target file.
        SSL_ENABLED (bool): Flag indicating whether SSL is enabled.
        SSL_CERT_PATH (str): The path to the SSL certificate file.
        SSL_KEY_PATH (str): The path to the SSL key file.
        LOG_FORMAT (str): The format for logging messages.
    """

    __logger = LoggingDescriptor("Configuration")

    def __init__(self, config_file: str = "config.ini") -> None:
        """Initializes the Configuration class by setting up the configuration
        parser and reading the config file.

        Args:
            config_file (str, optional): Config file name.
            Defaults to "config.ini".

        Examples:
        --------

        >>> config = Configuration()
        >>> config.HOST
        'localhost'
        >>> config.PORT
        43223
        >>> config.SSL_ENABLED
        False
        >>> config.SSL_CERT_PATH
        'ssl/cert/cert.pem'
        >>> config.SSL_KEY_PATH
        'ssl/key/key.pem'
        """
        # Initialize the parser and set the path to the config file
        self._config = ConfigParser()
        self._CONFIG_PATH = (
            Path(__file__).resolve().parent.parent / config_file
        )

        # Read configurations
        try:
            self._read_config()
            (  # Todo: Clean up
                masked_path := (
                    lambda path: '/'.join(
                        [
                            '*' * len(part)
                            for part in path.rsplit('/', 1)[0].split('/')
                        ]
                        + [path.rsplit('/', 1)[-1]]
                    )
                )(self.FILE_PATH)
            )
            self.__logger.debug(f"File masked location: {masked_path}")
        except NoOptionError as err:
            self.__logger.error(
                f"Reading `{config_file}` failed  with error: {err}"
            )
            sys.exit(-1)

        except NoSectionError as err:
            self.__logger.error(
                f"Reading `{config_file}` failed  with error: {err}"
            )
            sys.exit(-1)

    def _read_config(self) -> None:
        """
        Read the configuration file and update settings.
        """

        # Read the config file
        self._config.read(self._CONFIG_PATH)

        # Server Config
        self.HOST: str = "localhost"
        self.PORT: int = 43223

        # Re-Read on Query
        self.REREAD_ON_QUERY: bool = False

        # File Path
        self.FILE_PATH: str = self._config.get("DEFAULT", "linuxpath")

        # SSL Configuration
        self.SSL_ENABLED: bool = False
        self.SSL_CERT_PATH: str = self._config.get(
            "SSL", "cert_path", fallback="ssl/certs/cert.pem"
        )
        self.SSL_KEY_PATH: str = self._config.get(
            "SSL", "key_path", fallback="ssl/key/key.pem"
        )
