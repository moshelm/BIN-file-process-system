from pathlib import Path

from process_service.src.parsers.multiprocess_parser.process_stream import ParseMultiprocess, sum_msgs_formats


def test_sum_msgs_formats_counts_nonempty_items():
    assert sum_msgs_formats(["", "1", ""]) == 1


def test_parse_chunk_with_no_messages(tmp_path):
    empty_file = tmp_path / "empty.bin"
    empty_file.write_bytes(b"")
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()

    parser = ParseMultiprocess()
    count, wrong = parser.parse_chunk(
        str(empty_file),
        [None] * 256,
        [0] * 256,
        0,
        0,
        str(temp_dir),
    )

    assert count == 0
    assert wrong == []
