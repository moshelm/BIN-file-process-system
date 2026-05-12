
# ArduPilot Log Parsing Service

This microservice is built with **FastAPI** to process and analyze ArduPilot binary log files (`.bin`). It leverages multiple concurrency models and parsing strategies to ensure high performance and scalability.

## Service Flow

1.  **File Upload:** The user uploads a `.bin` file via the provided API endpoints.
2.  **Temporary Storage:** The file is saved asynchronously to a temporary directory for processing.
3.  **Orchestration:** The `Orchestrator` manages the execution of different parsing strategies.
4.  **Processing:** Data is extracted using either Threading (for I/O-bound tasks) or Multiprocessing (for CPU-bound parsing).
5.  **Response:** Results are returned as a real-time JSON stream or as a filtered downloadable file.

## Critical Data Schemas

The service uses standardized schemas to ensure consistent communication between the parsers and the API.

### ParseStatus (Enum)
Defines the state of a parsing operation.
* `SUCCESS`: The file was processed without critical errors.
* `FAILED`: An error occurred during the parsing lifecycle.

### ParseResult (Model)
The primary data structure returned by all parsing operations.
* `parser_name`: The specific parser implementation used (e.g., "multiprocess parser").
* `information`: Describes the parsing context or method.
* `duration`: The time taken to process the file (in seconds).
* `count`: The total number of messages successfully extracted.
* `status`: The `ParseStatus` (Success/Failed).
* `file_path`: Path to the source file or the resulting processed file.
* `json_file_result_name`: (Optional) The path to a generated JSONL result, used in filtered GPS queries.

## Parsing Strategies

The service implements three distinct parsing methods:
* **Pure Python Parser:** A high-performance manual implementation using `mmap` (Memory Mapping) and `struct` to read raw bytes.
* **Pymavlink Parser:** Uses the standard `pymavlink` library. It is highly reliable for standard Mavlink messages and specific filtering (like GPS data).
* **Multiprocess Parser:** Designed for large files. it splits the binary data into chunks and processes them across multiple CPU cores using `multiprocessing.Pool`, bypassing the Python GIL limitation.

## Concurrency and Performance

### Async/Await
FastAPI's asynchronous nature allows the service to handle multiple concurrent file uploads and streaming responses without blocking the main event loop.

### Threading
Since parsing is a CPU-intensive task, the `Orchestrator` uses `asyncio.to_thread` to move parsing logic off the main thread, keeping the API responsive.

### Multiprocessing
For heavy workloads, the `ParseMultiprocess` class utilizes a process pool to distribute the workload across available hardware cores, significantly reducing processing time for million-message logs.

## Endpoints

### `POST /process_file`
Executes all available parsers and streams the results.
* **Input:** Binary file (`.bin`).
* **Output:** A `StreamingResponse` of `ParseResult` objects in JSON format.

### `POST /process_gps_messages`
Filters the log for GPS-specific messages only.
* **Input:** Binary file (`.bin`).
* **Output:** A `.jsonl` file containing filtered GPS telemetry (Lat, Lng, Alt, Spd) with statistical headers.

### `GET /health`
Standard health check to monitor service availability.