# Parser Refactor Summary

## Goal
Refactor the ArduPilot binary parser so the pure Python parser and the multiprocessing parser share the same parsing engine.

## Changes

- `process_service/src/parsers/pure_py_parser.py`
  - Added shared core classes:
    - `MessageSchema`
    - `SchemaBuilder`
    - `BinaryDecoder`
    - `ChunkParser`
  - `PurePythonParser` now uses the shared schema builder and binary decoder directly.
  - All struct and string decoding logic is centralized here.

- `process_service/src/parsers/multiprocess_parser/process_stream.py`
  - Worker processes now receive only `file_path`, `start`, `end`, and optional message filters.
  - Each worker scans the binary file locally and builds its own schemas.
  - No `struct.Struct`, namedtuple, or schema objects are passed between processes.
  - Multiprocessing is now orchestration-only.

- `process_service/src/parsers/multiprocess_parser/parse_file_config.py`
  - Simplified `ArduPilotParser` to build only picklable metadata when needed.
  - Shared logic is reused from `SchemaBuilder`.

## Why this solves the duplication and pickle problem

- The shared core lives in `pure_py_parser.py`, so both parsers reuse the same schema building and decode logic.
- Multiprocess workers reconstruct `struct.Struct` and namedtuple classes locally from `file_path`.
- The main process only sends primitive chunk metadata, not pickle-sensitive parser objects.

## Result
- Cleaner, DRY architecture.
- Same external parser behavior retained.
- Multiprocessing now only coordinates workers, while workers parse independently.
