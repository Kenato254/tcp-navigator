import socket
import ssl

from ..configuration import Configuration
from .helpers.logging_helper import LoggingDescriptor


class TcpClient:
    """Handles a secure TCP client connection for sending queries to a server.

    Attributes:
        __logger (LoggingDescriptor): Logger instance for logging class events.
        host (str): Server host address.
        port (int): Server port number.
        context (Optional[ssl.SSLContext]): SSL context for secure connection.
        connection (socket.socket): Socket connection to the server.
    """

    __logger = LoggingDescriptor("TcpClient")

    def __init__(self, config: Configuration):
        """Initializes TCP client with configuration and connects to the
        server.

        Args:
            config (Configuration): Configuration for host, port, and SSL
            settings.

        Raises:
            socket.error: Logs and exits if connection fails.
        """
        # Todo: Needs validators
        self.host = config.HOST
        self.port = config.PORT

        # Create SSL context if enabled
        if config.SSL_ENABLED:
            self.context = ssl.create_default_context(
                ssl.Purpose.SERVER_AUTH
            )
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE

        # Create socket and connect to a running server
        try:
            self.connection = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )

            # Enable secure client's communication with server
            if config.SSL_ENABLED:
                self.connection = self.context.wrap_socket(
                    self.connection, server_hostname=self.host
                )
            self.__logger.info("Socket created successfully for Client")

            # Connect to the host
            self.connection.connect((self.host, self.port))
            self.__logger.info(
                f"Connected to server at {self.host}:{self.port}"
            )
        except socket.error as err:
            self.__logger.error(f"Connection error: {err}")

    def send_queries(self) -> None:
        """Sends queries to the server, retrieving responses, until
        'quit' or 'stop' is issued.

        Logs each server response or client exit.

        Raises:
            KeyboardInterrupt: Logs and closes connection if
                interrupted by user.
        """

        self.__logger.info("Ready to send queries. Type 'quit' to exit.")
        try:
            while True:
                # Query input
                query = input(
                    "Enter query (or type 'quit' or 'exit' to exit): "
                ).strip()

                # Stop client when 'quit' or 'stop' in query
                if query.lower() in ("quit", "exit"):
                    self.__logger.info("Shutting down client...")
                    break

                if not query == "":
                    # Prepare query for submission
                    query_submission = query.encode("utf-8")
                    # Submit query
                    self.connection.send(query_submission)
                    # Receive query result from server
                    response = (
                        self.connection.recv(1024).decode("utf-8").strip()
                    )
                    self.__logger.info(f"Server Response: {response}")
                else:
                    self.__logger.warning(
                        "Query empty (type 'quit' or 'exit' to exit)"
                    )

        except KeyboardInterrupt:
            self.__logger.info("Client interrupted by user.")
        finally:
            self.close_connection()

    def close_connection(self) -> None:
        """
        Closes the client connection if it is open and logs the closure.
        """
        if self.connection:
            self.connection.close()
            self.__logger.info("Connection to server closed.")


if __name__ == "__main__":
    config = Configuration()
    client = TcpClient(config)
    client.send_queries()
