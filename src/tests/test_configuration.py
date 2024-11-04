from configparser import NoOptionError, NoSectionError
from unittest.mock import MagicMock, patch

import pytest

from ..configuration import Configuration


@patch(
    "src.configuration.ConfigParser.get",
    side_effect=NoOptionError(section="DEFAULT", option="option"),
)
def test_configuration_missing_option(mock_get: MagicMock) -> None:
    with pytest.raises(SystemExit):
        Configuration()


@patch(
    "src.configuration.ConfigParser.get",
    side_effect=NoSectionError("DEFAULT"),
)
def test_configuration_missing_section(mock_get: MagicMock) -> None:
    with pytest.raises(SystemExit):
        Configuration("config.ini")
