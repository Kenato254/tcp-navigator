import socket
import ssl
import sys
from unittest.mock import MagicMock, patch

import pytest

from ..configuration import Configuration
from ..core.server import TcpServer


class ExitException(Exception):
    """Custom exception to simulate sys.exit in tests."""

    pass


@pytest.fixture
def mock_file_loader() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_config() -> Configuration:
    config = MagicMock(spec=Configuration)
    config.HOST = '127.0.0.1'
    config.PORT = 12345
    config.SSL_ENABLED = False
    config.SSL_CERT_PATH = "ssl/cert.pem"
    config.SSL_KEY_PATH = "ssl/key.pem"
    return config


@pytest.fixture
def mock_load_cert_chain() -> MagicMock:
    return MagicMock()


@patch("src.core.server.ssl.create_default_context")
@patch("src.core.server.TcpRequestHandler")
@patch("src.core.server.ThreadedTcpServer")
def test_tcp_server_initialization(
    mock_server_class: MagicMock,
    mock_handler_class: MagicMock,
    mock_ssl_context: MagicMock,
    mock_config: Configuration,
    mock_file_loader: MagicMock,
) -> None:
    server_instance = mock_server_class.return_value
    TcpServer(mock_config, mock_file_loader)

    mock_server_class.assert_called_once_with(
        (mock_config.HOST, mock_config.PORT),
        mock_handler_class,
        mock_file_loader,
    )
    assert server_instance.server is not None


@patch("ssl.create_default_context")
def test_tcp_server_init_bind_success(
    mock_create_default_context: MagicMock,
    mock_load_cert_chain: MagicMock,
    mock_config: Configuration,
) -> None:
    """Test that the TcpServer initializes and binds successfully with SSL."""

    # Configure mock SSL context and load_cert_chain method
    mock_ssl_context = mock_create_default_context.return_value
    mock_ssl_context.load_cert_chain = mock_load_cert_chain

    # Create a mock FileLoader instance
    mock_file_loader = MagicMock()

    # Initialize TcpServer
    server = TcpServer(mock_config, mock_file_loader)

    # Verify server's host and port are set as expected
    assert server.host == "127.0.0.1"
    assert server.port == 12345

    # Check that the server's SSL context was created
    mock_create_default_context.assert_called_once()


@patch("src.core.server.ThreadedTcpServer")
@patch("src.core.server.ssl.SSLContext.wrap_socket")
@patch("src.core.server.ssl.SSLContext.load_cert_chain")
@patch("src.core.server.random.randint", return_value=54321)
def test_bind_server_socket_error(
    mock_randint: MagicMock,
    mock_load_cert_chain: MagicMock,
    mock_wrap_socket: MagicMock,
    mock_threaded_server: MagicMock,
    monkeypatch: MagicMock,
    mock_config: Configuration,
    mock_file_loader: MagicMock,
) -> None:
    """Test TcpServer bind_server with socket.error edge case."""

    # Replace sys.exit with a custom exception
    monkeypatch.setattr(
        sys,
        "exit",
        lambda x: (_ for _ in ()).throw(ExitException("Mock exit")),
    )

    # Configure mock server to raise socket.error on binding
    mock_threaded_server.side_effect = socket.error("Port in use")

    # Expect ExitException due to sys.exit being called after retries
    with pytest.raises(ExitException, match="Mock exit"):
        server = TcpServer(mock_config, mock_file_loader)  # noqa: F841


@patch("src.core.server.ssl.create_default_context")
@patch("src.core.server.ThreadedTcpServer")
def test_tcp_server_run(
    mock_server_class: MagicMock,
    mock_create_default_context: MagicMock,
    mock_load_cert_chain: MagicMock,
    mock_config: Configuration,
    mock_file_loader: MagicMock,
) -> None:
    # Configure mock for SSL context and load_cert_chain method
    mock_ssl_context = mock_create_default_context.return_value
    mock_ssl_context.load_cert_chain = mock_load_cert_chain

    # Initialize TcpServer instance with mock config and file loader
    server = TcpServer(mock_config, mock_file_loader)

    # Run the server
    server.run()

    mock_server_class.return_value.serve_forever.assert_called_once()


@patch("src.core.server.ssl.create_default_context")
@patch("src.core.server.ThreadedTcpServer")
def test_tcp_server_shutdown(
    mock_server_class: MagicMock,
    mock_create_default_context: MagicMock,
    mock_load_cert_chain: MagicMock,
    mock_config: Configuration,
) -> None:
    # Configure the mock for SSL context
    mock_ssl_context = mock_create_default_context.return_value
    mock_ssl_context.load_cert_chain = mock_load_cert_chain

    # Create mock FileLoader instance
    mock_file_loader = MagicMock()

    # Instantiate TcpServer with the mocked config and file loader
    server = TcpServer(mock_config, mock_file_loader)

    # Call shutdown_server to test SSL-related cleanup without
    # starting the server
    server.shutdown_server()

    # Assertions to confirm that shutdown and close were called
    server_instance = mock_server_class.return_value
    server_instance.shutdown.assert_called_once()
    server_instance.server_close.assert_called_once()


@patch("src.core.server.ssl.create_default_context")
@patch("src.core.server.ThreadedTcpServer")
def test_ssl_enabled(
    mock_server_class: MagicMock,
    mock_create_default_context: MagicMock,
    mock_load_cert_chain: MagicMock,
    mock_config: Configuration,
) -> None:
    # Configure the mock for SSL context
    mock_ssl_context = mock_create_default_context.return_value
    mock_ssl_context.load_cert_chain = mock_load_cert_chain

    # Create mock FileLoader instance
    mock_file_loader = MagicMock()

    # Instantiate TcpServer with the mocked config and file loader
    server = TcpServer(mock_config, mock_file_loader)

    server.shutdown_server()

    # Assertions to confirm that shutdown and close were called
    server_instance = mock_server_class.return_value
    server_instance.shutdown.assert_called_once()
    server_instance.server_close.assert_called_once()

    # Assertions to ensure behavior
    mock_create_default_context.assert_called_once_with(
        ssl.Purpose.CLIENT_AUTH
    )
    mock_load_cert_chain.assert_called_once_with(
        certfile="ssl/cert.pem",
        keyfile="ssl/key.pem",
    )
