import random
import socket
import ssl
import sys
import time
from socketserver import BaseRequestHandler, TCPServer, ThreadingMixIn
from typing import Optional, Tuple, Type

from ..configuration import Configuration
from ..constants import SearchAlgorithm  # noqa: F401
from .helpers.file_loader import FileLoader
from .helpers.logging_helper import LoggingDescriptor


class TcpRequestHandler(BaseRequestHandler):
    """Handles client requests for file data presence using FileLoader.

    Attributes:
        __logger (LoggingDescriptor): Logger instance for logging class events.
    """

    __logger = LoggingDescriptor("TcpRequestHandler")

    def handle(self) -> None:
        """Handles incoming queries from a connected client.

        Processes each query and sends back a response.
        """
        # Access the FileLoader instance from the server
        file_loader = self.server.file_loader  # type: ignore

        try:
            client_ip = self.client_address[0]
            self.__logger.info(
                f"Connected to client {client_ip}:{self.client_address[1]}"
            )

            while True:
                query = self.request.recv(1024).decode("utf-8").strip()

                if not query:
                    break

                # Start performance counter
                start_perf_counter = time.perf_counter()

                # Use FileLoader to check the file
                if file_loader.check_text(query.encode()):
                    response = "STRING EXISTS\n"
                else:
                    response = "STRING NOT FOUND\n"

                end_perf_counter = time.perf_counter()
                execution_time = (
                    end_perf_counter - start_perf_counter
                ) * 1_000

                self.__logger.debug(
                    (
                        f"Query: {query} - Client IP: {client_ip}"
                        f"- Execution Time: {execution_time:.2f} ms"
                    )
                )

                self.request.sendall(response.encode("utf-8"))

        except socket.error as err:
            self.__logger.error(f"Error handling client query: {err}")

        except IndexError as err:
            self.__logger.warning(
                f"Incomplete client's connection response: {err}"
            )


class ThreadedTcpServer(ThreadingMixIn, TCPServer):
    """Multithreaded TCP server that assigns each client to a separate thread.

    Attributes:
        allow_reuse_address (bool): Enables address reuse.
        file_loader (FileLoader): Instance used for file operations.
    """

    allow_reuse_address: bool = True

    def __init__(
        self,
        server_address: Tuple[str, int],
        RequestHandlerClass: Type[BaseRequestHandler],
        file_loader: FileLoader,
    ):
        """Initializes the server with address, handler, and FileLoader.

        Args:
            server_address (Tuple[str, int]): Tuple of server host and port.
            RequestHandlerClass (Type[BaseRequestHandler]): Class for handling
                                                            requests.
            file_loader (FileLoader): Instance for file operations.
        """

        super().__init__(server_address, RequestHandlerClass)
        self.file_loader: FileLoader = file_loader


class TcpServer:
    """Manages a TCP server with optional SSL, handling connections
    and file operations.

    Attributes:
        __logger (LoggingDescriptor): Logger for class events.
        host (str): Server host.
        port (int): Server port.
        context (ssl.SSLContext): SSL context for secure communication.
        _file_loader (FileLoader): Instance to manage file operations.
    """

    __logger = LoggingDescriptor("TcpServer")

    def __init__(self, config: Configuration, file_loader: FileLoader):
        """Initializes the TCP server with a specified host and port.
        If the port is in use, it will attempt to bind to an available port.

        Args:
            config (Configuration): Configuration object containing server
            settings.

            file_loader (FileLoader): FileLoader instance for handling file
            operations.

        Raises:
            FileNotFoundError: Exit if `SSL_ENABLE=True` and cryptographic
            credentials configuration properties are missing.
        """
        # Todo: Needs validators
        self.host = config.HOST
        self.port = config.PORT
        self._ssl_enabled = config.SSL_ENABLED

        try:
            # SSL context setup
            self.context = ssl.create_default_context(
                ssl.Purpose.CLIENT_AUTH
            )

            self.context.load_cert_chain(
                certfile=config.SSL_CERT_PATH,
                keyfile=config.SSL_KEY_PATH,
            )
        except FileNotFoundError as err:
            self.__logger.error(
                (
                    f"SSL enabled 'load_cert_chain' failed with {err}"
                    " for ssl 'certificate' or 'primary key' "
                )
            )
            # Stop server
            sys.exit(-1)

        self._file_loader = file_loader
        self.server: Optional[ThreadedTcpServer] = None

        self.bind_server()

    def bind_server(self) -> None:
        """Binds the server to the specified host and port,retrying
        with random ports if necessary.

        Incase one of the error is raised, retry steps in 5 times, then exits
        if unsuccessful.

        Raises:
            socket.error: Logs error if binding failes due to
                          illigal host or in-use port.

        Raises:
            AttributeError: Logs error if configuration properties are missing.
        """
        retry_mechanism: int = 0

        while True:
            # Retry mechanism for first 5 failed binding attempts
            if retry_mechanism > 5:
                sys.exit(-1)

            try:
                # Pass FileLoader instance to ThreadedTcpServer
                self.server = ThreadedTcpServer(
                    (self.host, self.port),
                    TcpRequestHandler,
                    self._file_loader,
                )

                # Enable SSL
                if self._ssl_enabled:
                    self.server.socket = self.context.wrap_socket(
                        self.server.socket, server_side=True
                    )

                self.__logger.info(
                    f"Server listening on {self.host}:{self.port}"
                )
                break
            except socket.error as err:
                self.__logger.error(
                    (
                        f"Binding failed on {self.host}"
                        f":{self.port} with error: {err}"
                    )
                )
                self.__logger.info(
                    f"Retrying with random port {self.port}"
                )
                if "Port in use" in str(err):
                    self.port = random.randint(1024, 65535)
            except AttributeError as err:
                self.__logger.error(
                    f"Setting instance attributes failed with: {err}"
                )
            retry_mechanism += 1

    def run(self) -> None:
        """Runs the server, handling client connections in separate threads.

        Raises:
            KeyboardInterrupt: Logs error and shutdowns server if Ctrl+C is
                press.
        """

        try:
            self.__logger.info("Server is running. Press Ctrl+C to stop.")
            self.server.serve_forever()  # type: ignore
        except KeyboardInterrupt:
            self.__logger.info("Server shutting down on user request.")
        finally:
            self.shutdown_server()

    def shutdown_server(self) -> None:
        """Shuts down and closes the server socket, freeing the port."""

        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.__logger.info("Server socket closed and port released.")


if __name__ == "__main__":
    config = Configuration()
    file_loader = FileLoader(config)
    if (
        not config.REREAD_ON_QUERY
    ):  # Todo: Run on a seperate thread to avoid blocking
        file_loader.load_buffer()

    server = TcpServer(config, file_loader)
    server.run()
