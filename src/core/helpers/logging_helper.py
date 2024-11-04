import logging
from typing import Optional


class LoggingDescriptor:
    """
    Descriptor class for logging functionality in classes.

    Attributes:
        name (str): The name of the logger, typically the class name.
        logger (Logger): Instance of the logger class.
    """

    def __init__(self, name: str):
        """
        Initializes the logger with a specified name.

        Args:
            name (str): The name to assign to the logger instance.
        """

        self.name = name
        self.logger = self._create_logger(name)

    def _create_logger(self, name: str) -> logging.Logger:
        """Creates a logger for owner class.

        Args:
            name (str): The name of the logger, typically the class name.

        Returns:
            logging.Logger: Logger instance named after the owner class.
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        format_str = (
            "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s"
        )

        formatter = logging.Formatter(
            format_str, datefmt="%Y-%m-%d %H:%M:%S"
        )
        ch.setFormatter(formatter)

        if not logger.hasHandlers():
            logger.addHandler(ch)

        return logger

    def __get__(
        self, instance: object, owner: Optional[type] = None
    ) -> logging.Logger:
        """
        Retrieves the logger instance for the owner class.

        Args:
            instance (Any): The instance accessing this descriptor.
            owner (Type): The owner class.

        Returns:
            logging.Logger: Logger instance named after the owner class.
        """

        return self.logger
