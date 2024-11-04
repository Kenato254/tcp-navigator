# TCP Navigator

**TCP Navigator** is a multithreaded TCP server application designed to handle concurrent client connections, search strings within a specified file, and return query results based on specified configurations. The server supports both static and dynamic file reads, SSL configuration, and real-time file querying based on client requests.

## Table of Contents

- [TCP Navigator](#tcp-navigator)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Features](#features)
  - [Project Structure](#project-structure)
  - [Configuration](#configuration)
    - [Important Configuration Options](#important-configuration-options)
  - [Installation](#installation)
    - [Option 1: Using Poetry](#option-1-using-poetry)
    - [Option 2: Using pip and venv](#option-2-using-pip-and-venv)
  - [Usage](#usage)
  - [Benchmark Report Summary](#benchmark-report-summary)
    - [Objective](#objective)
    - [Algorithms Tested](#algorithms-tested)
    - [Some Results Summary](#some-results-summary)
    - [Conclusions](#conclusions)
  - [Development Notes](#development-notes)

## Project Overview

TCP Navigator is a multithreaded server application that binds to a specified port and listens for incoming client connections. It accepts client queries, searches for an exact match within a specified file, and returns either `"STRING EXISTS"` or `"STRING NOT FOUND"` as the response. The project includes configurable options for file reading behavior (`REREAD_ON_QUERY`), SSL encryption, and logging.

---
## Features

- **Concurrent Connections**: The server can handle unlimited concurrent connections using multithreading.
- **Configurable File Reads**:
  - **`REREAD_ON_QUERY`**: If set to `True`, the file is re-read for each client query. If `False`, the file is loaded once at startup and stored in memory.
- **Exact String Matching**: The server searches for a complete line match of the client's query in the specified file.
- **Configurable SSL/TLS Support**: The server supports SSL encryption, with paths to SSL certificates specified in the configuration.
---
## Project Structure

```
tcp_navigator/
├── config.ini                 # Configuration file for server settings
├── docs                       # Documentation files
├── src                        # Source code
│   ├── configuration.py       # Configuration management
│   ├── constants.py           # Constants and enumerations
│   ├── core
│   │   ├── client.py          # TCP client implementation
│   │   ├── server.py          # TCP server implementation
│   │   ├── helpers
│   │   │   ├── file_loader.py # File loader with search algorithms
│   │   │   ├── logging_helper.py # Logger setup helper
│   └── tests                  # Unit and performance tests
│       ├── test_client.py     # Client tests
│       ├── test_server.py     # Server tests
└── ssl                        # SSL certificates
    ├── cert.pem               # SSL certificate
    └── key.pem                # SSL private key
```

---
## Configuration

The application’s behavior is controlled by a configuration file (`config.ini`), which contains essential settings such as the `FILE_PATH`, `SSL` configuration, and `SERVER_CONFIG`. The `REREAD_ON_QUERY` flag is located inside `Configuration` class to improve `bool` type precision.

### Important Configuration Options 
- *`config.ini`:*
	- **`linuxpath`** (**FILE_PATH**): Path to the file where the server will search for query matches.
	- **`host`** (**SERVER_CONFIG**): String containing the server's address.
	- **`port`** (**SERVER_CONFIG**): Integer value of the server's port.
	- **`cert_path`** (**SSL**): Path to the ssl certificate.
	- **`key_path`** (**SSL**): Path to the ssl private key.

- *`configuration.Configuration`*: 
	- **`REREAD_ON_QUERY`**: If set to `True`, the file is re-read for each query. If set to `False`, the file is loaded once on server startup.
	- **`SSL_ENABLED`**: Enables or disables SSL.
	- **`SSL_CERT_PATH`** and **`SSL_KEY_PATH`**: Paths to the SSL certificate and key files. Correspond to `config.ini` configurations.
	- **`HOST`** and **`PORT`**:  Correspond to host and port configured in the `config.ini`


## Installation

1. **Unzip the Repository**:
   - Navigate to the `tcp_navigator` directory if you are not already there:
   ```bash
   cd tcp_navigator
   ```

2. **Set Up a Virtual Environment**:
   Choose either **Poetry** or **pip** to set up a virtual environment.

   ### Option 1: Using Poetry

   - Ensure you have Poetry installed (you can install it from [here](https://python-poetry.org/docs/#installation)).
   - Create a virtual environment and install dependencies:
     ```bash
     poetry install
     ```
   - Activate the virtual environment:
     ```bash
     poetry shell
     ```

   ### Option 2: Using pip and venv

   - Ensure you have Python 3.10+ installed, then create a virtual environment:
     ```bash
     python3 -m venv venv
     ```
   - Activate the virtual environment:
     - On macOS/Linux:
       ```bash
       source venv/bin/activate
       ```
    
   - Install required libraries:
     ```bash
     pip install -r requirements.txt
     ```

3. **Set Up SSL (Optional)**:
   If using SSL, place your SSL certificate and key files in the paths specified in `config.ini`:

```ini
	[SSL]
	cert_path=ssl/cert/cert.pem
	key_path=ssl/key/key.pem
```

4. **Edit Configuration File**:
   Update the `config.ini` file as needed.

---
## Usage

1. **Run tests:**
```sh 
	pytest src/tests -v 
```

2. **Start the Server**:
```bash
   python -m src.core.server
```

3. **Send Client Queries**:
   The server listens for incoming client queries on the specified port. Use a TCP client to connect and send queries.

4. **Start the client**
```sh
	python -m src.core.client
```

5. **Alternatively, use `nc` as a TCP Client **:
```bash
   echo "query_string" | nc localhost <PORT>
```


---
## Benchmark Report Summary

### Objective
To benchmark multiple file-search algorithms and determine the most efficient for large files on Linux.

### Algorithms Tested

1. **Low-Level File Search (mmap + os)**: Direct memory-mapped access for optimized low-level reading.
2. **High-Level File Search (open + mmap)**: Higher-level file reading with memory-mapping.
3. **Brute-Force Line-by-Line Search**: Sequentially reads each line.
4. **Regex-Based Search**: Allows complex pattern matching.
5. **Linux `grep` Command**: Highly optimized for text search.

### Some Results Summary

| Algorithm          | Rows (10K) | Rows (50K) | Rows (100K) | Rows (250K) | Rows (500K) | Rows (1M) |
| ------------------ | ---------- | ---------- | ----------- | ----------- | ----------- | --------- |
| Grep (Linux)       | 3.4 ms     | 4.4 ms     | 6.8 ms      | 7.0 ms      | 14.7 ms     | 27.5 ms   |
| Regex Search       | 2.1 ms     | 4.0 ms     | 8.0 ms      | 14.0 ms     | 25.0 ms     | 46.0 ms   |
| Brute-Force Search | 5.8 ms     | 15.7 ms    | 27.6 ms     | 47.6 ms     | 100.5 ms    | 269.8 ms  |

---
### Conclusions
- **Best Overall Performance**: The Linux `grep` command.
- **Optimal Pattern Matching**: Regex-based search for complex queries.
- **Caching Impact**: With `REREAD_ON_QUERY` enabled, lookups average **0.02 ms** due to constant-time hashmap access.

---

## Development Notes

- **Testing**: Unit tests cover both server and client functionality, multithreading performance, and exception handling.
- **TCP Logging**: Captures client details, query text, and execution time for each request.
- **SSL Support**: Optional SSL enables secure client-server communication.
- **Caching**: For static data, enabling `REREAD_ON_QUERY` significantly improves search speed by caching file content.
