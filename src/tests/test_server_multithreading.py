import socket
import threading
import time
from typing import Generator, Tuple
from unittest.mock import MagicMock

import pytest

from src.configuration import Configuration
from src.core.helpers.file_loader import FileLoader
from src.core.server import TcpRequestHandler, ThreadedTcpServer


@pytest.fixture
def config() -> Configuration:
    """Fixture to load configuration for server testing."""
    config = Configuration()
    config.HOST = "127.0.0.1"
    config.PORT = 0  # Bind to any available port for test
    config.SSL_ENABLED = False
    return config


@pytest.fixture
def file_loader() -> MagicMock:
    """Fixture to create a mock FileLoader for testing."""
    mock_loader = MagicMock(spec=FileLoader)
    mock_loader.check_text.return_value = True
    return mock_loader


@pytest.fixture
def threaded_tcp_server(
    config: Configuration, file_loader: MagicMock
) -> Generator[ThreadedTcpServer, None, None]:
    """Fixture to initialize and run ThreadedTcpServer for testing."""
    server_address: Tuple[str, int] = (config.HOST, config.PORT)
    server = ThreadedTcpServer(
        server_address, TcpRequestHandler, file_loader
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server
    server.shutdown()


def test_concurrent_client_requests(
    threaded_tcp_server: ThreadedTcpServer, file_loader: MagicMock
) -> None:
    """
    Test server's ability to handle multiple client requests concurrently.
    """
    clients: list[socket.socket] = []
    num_clients: int = 5

    def client_thread(client_socket: socket.socket) -> None:
        """Simulates a client sending a request and receiving a response."""
        try:
            client_socket.connect((threaded_tcp_server.server_address))
            client_socket.sendall(b"test")
            response = client_socket.recv(1024)
            assert response == b"STRING EXISTS"
        finally:
            client_socket.close()

    for _ in range(num_clients):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clients.append(client_socket)
        threading.Thread(
            target=client_thread, args=(client_socket,), daemon=True
        ).start()

    time.sleep(1)  # Allow time for threads to execute
    file_loader.check_text.assert_called_with(b"test")
    assert len(clients) == num_clients


def test_sequential_client_requests(
    threaded_tcp_server: ThreadedTcpServer, file_loader: MagicMock
) -> None:
    """
    Test server's ability to handle sequential requests from a single client.
    """
    with socket.create_connection(
        threaded_tcp_server.server_address  # type: ignore
    ) as client_socket:
        for query in [b"test1", b"test2", b"test3"]:
            client_socket.sendall(query)
            response = client_socket.recv(1024)
            assert response == b"STRING EXISTS"
            file_loader.check_text.assert_any_call(query)
