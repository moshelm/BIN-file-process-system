import os
import struct
import tempfile

import pytest

from process_service.src.parsers.pure_py_parser import PurePythonParser, get_message_information_by_name
from shared.schemas import ParseStatus


def test_build_struct_from_format_valid():
    parser = PurePythonParser()
    struct_obj = parser.build_struct_from_format("BB")

    assert isinstance(struct_obj, struct.Struct)
    assert struct_obj.format == "<BB"


def test_build_struct_from_format_invalid():
    parser = PurePythonParser()

    with pytest.raises(ValueError):
        parser.build_struct_from_format("X")


def test_parse_file_rows_returns_no_messages_for_empty_file(tmp_path):
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")

    parser = PurePythonParser()
    assert list(parser.parse_file_rows(str(path))) == []


def test_parse_file_returns_failed_for_empty_file(tmp_path):
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")

    result = PurePythonParser().parse_file(str(path))

    assert result.status == ParseStatus.FAILED


def test_get_message_information_by_name_returns_none():
    assert get_message_information_by_name([None, None], "unknown") is None


def test_parse_file_with_debug_flag(tmp_path, capsys):
    """Test that parse_file accepts debug flag without error"""
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")

    result = PurePythonParser().parse_file(str(path), debug=True)
    assert result.status == ParseStatus.FAILED

