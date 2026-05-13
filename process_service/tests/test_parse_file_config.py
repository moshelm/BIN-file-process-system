import tempfile

import pytest

from process_service.src.parsers.multiprocess_parser.parse_file_config import ArduPilotParser


def test_serialize_to_python_format_valid():
    parser = ArduPilotParser()
    assert parser.serialize_to_python_format("IB") == "<IB"


def test_serialize_to_python_format_invalid():
    parser = ArduPilotParser()

    with pytest.raises(ValueError):
        parser.serialize_to_python_format("X")


def test_scan_fmt_messages_returns_empty_for_nonmatching_file(tmp_path):
    file_path = tmp_path / "payload.bin"
    file_path.write_bytes(b"not a valid header")

    parser = ArduPilotParser()
    assert parser.scan_fmt_messages(str(file_path)) == {}


def test_get_formats_and_length_messages_returns_tuple(tmp_path):
    file_path = tmp_path / "payload.bin"
    file_path.write_bytes(b"not a valid header")

    parser = ArduPilotParser()
    formats, lens = parser.get_formats_and_length_messages(str(file_path))

    assert isinstance(formats, list)
    assert isinstance(lens, list)
    assert len(formats) == 256
    assert len(lens) == 256
