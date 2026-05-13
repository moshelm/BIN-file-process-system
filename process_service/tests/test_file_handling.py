import os
import pickle
import tempfile
from pathlib import Path

import pytest

from process_service.src.utils.file_handling import (
    close_temp_file,
    combine_files_zero_copy,
    create_temporary_file,
    get_size_file,
    remove_temp_file,
    write_to_temp_file_pickle,
)


def test_create_and_close_temp_file():
    temp_file = create_temporary_file()
    assert temp_file.name.endswith(".jsonl")
    close_temp_file(temp_file)
    assert os.path.exists(temp_file.name)
    remove_temp_file(temp_file.name)
    assert not os.path.exists(temp_file.name)


def test_combine_files_zero_copy(tmp_path):
    file_a = tmp_path / "a.bin"
    file_b = tmp_path / "b.bin"
    file_a.write_bytes(b"hello")
    file_b.write_bytes(b"world")
    combined_path = tmp_path / "combined.bin"

    combine_files_zero_copy(str(combined_path), [str(file_a), str(file_b)])

    assert combined_path.read_bytes() == b"helloworld"
    assert not file_a.exists()
    assert not file_b.exists()


def test_write_to_temp_file_pickle_and_get_size_file(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    temp_file_path = write_to_temp_file_pickle(str(temp_dir), [1, 2, 3])

    assert Path(temp_file_path).exists()
    assert get_size_file(temp_file_path) > 0

    with open(temp_file_path, "rb") as f:
        assert pickle.load(f) == [1, 2, 3]

    remove_temp_file(temp_file_path)
    assert not Path(temp_file_path).exists()


async def test_create_and_write_new_file_to_disc_async(tmp_path):
    from io import BytesIO
    from fastapi import UploadFile
    from process_service.src.utils.file_handling import create_and_write_new_file_to_disc_async

    destination = tmp_path / "uploaded.bin"
    upload = UploadFile(filename="uploaded.bin", file=BytesIO(b"binary data"))

    await create_and_write_new_file_to_disc_async(upload, str(destination))
    assert destination.read_bytes() == b"binary data"

    await upload.close()
