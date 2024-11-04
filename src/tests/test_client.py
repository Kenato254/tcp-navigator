import socket
from unittest.mock import MagicMock, patch

import pytest

from src.configuration import Configuration
from src.core.client import TcpClient


@pytest.fixture
def mock_config() -> Configuration:
    config = MagicMock(spec=Configuration)
    config.HOST = '127.0.0.1'
    config.PORT = 12345
    config.SSL_ENABLED = False
    return config


@patch("src.core.client.socket.socket")
@patch("src.core.client.ssl.create_default_context")
def test_tcp_client_connection_without_ssl(
    mock_ssl_context: MagicMock,
    mock_socket: MagicMock,
    mock_config: Configuration,
) -> None:
    # Mock the socket instance
    mock_socket_inst = mock_socket.return_value

    # Initialize the TcpClient without SSL
    client = TcpClient(mock_config)

    # Assert that the socket was created with the correct parameters
    mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)

    # Assert that the client connected to the correct host and port
    mock_socket_inst.connect.assert_called_once_with(
        (mock_config.HOST, mock_config.PORT)
    )

    # Assert that the client's connection attribute is set correctly
    assert client.connection == mock_socket_inst


@patch("src.core.client.socket.socket")
@patch("src.core.client.ssl.create_default_context")
def test_tcp_client_connection_with_ssl(
    mock_ssl_context: MagicMock,
    mock_socket: MagicMock,
    mock_config: Configuration,
) -> None:
    # Enable SSL in the mock configuration
    mock_config.SSL_ENABLED = True

    # Mock the SSL context's wrap_socket method to
    # return the mock socket
    mock_ssl_context.return_value.wrap_socket.return_value = (
        mock_socket.return_value
    )

    # Initialize the TcpClient with SSL
    client = TcpClient(mock_config)  # noqa: F841

    # Assert that the SSL context was created
    mock_ssl_context.assert_called_once()

    # Assert that the client connected
    # to the correct host and port
    mock_socket.return_value.connect.assert_called_once_with(
        (mock_config.HOST, mock_config.PORT)
    )


@patch("src.core.client.socket.socket")
@patch("builtins.input", side_effect=["test", "quit"])
def test_tcp_client_send_queries(
    mock_input: MagicMock,
    mock_socket: MagicMock,
    mock_config: Configuration,
) -> None:
    # Initialize the TcpClient
    client = TcpClient(mock_config)

    # Mock the client's connection attribute
    client.connection = MagicMock()

    # Call the send_queries method
    client.send_queries()

    # Assert that the client sent the correct query
    client.connection.send.assert_called_once_with(b"test")

    # Assert that the client received a response
    client.connection.recv.assert_called_once()


@patch("src.core.client.socket.socket")
def test_tcp_client_close_connection(
    mock_socket: MagicMock, mock_config: Configuration
) -> None:
    # Initialize the TcpClient
    client = TcpClient(mock_config)

    # Mock the client's connection attribute
    client.connection = MagicMock()

    # Call the close_connection method
    client.close_connection()

    # Assert that the client closed the connection
    client.connection.close.assert_called_once()
