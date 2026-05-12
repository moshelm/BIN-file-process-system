import os
import pickle
import shutil
import tempfile
import uuid
from pathlib import Path
from tempfile import _TemporaryFileWrapper

import aiofiles
from fastapi import UploadFile

from shared.logger_config import get_logger

logger = get_logger(__name__)


async def create_and_write_new_file_to_disc_async(file: UploadFile, temp_file_name: str) -> None:
    try:
        file_path = Path(temp_file_name)
        if file_path.exists() and file_path.stat().st_size > 0:
            logger.info(f"File {temp_file_name} already exists and is not empty. Skipping write.")
            return
        async with aiofiles.open(temp_file_name, "ab") as f:
            context: bytes = await file.read()
            await f.write(context)
    except Exception:
        logger.error("failed write new file to disc", exc_info=True)
        raise


def create_temporary_file() -> _TemporaryFileWrapper:
    return tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl", mode="w", encoding="utf-8")


def close_temp_file(file: _TemporaryFileWrapper) -> None:
    if file:
        file.close()


def remove_temp_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logger.info(f"Deleted temp file: {path}")
    except Exception as e:
        logger.error(f"Failed to delete temp file {path}: {e}")


def combine_files_zero_copy(combined_file_path: str, temp_files: list) -> None:
    with open(combined_file_path, "wb") as outfile:
        for tf in temp_files:
            with open(tf, "rb") as infile:
                shutil.copyfileobj(infile, outfile)
            os.remove(tf)


def write_to_temp_file_pickle(temp_dir: str, msgs: list) -> str:
    temp_filename = os.path.join(temp_dir, f"chunk_{uuid.uuid4().hex}.pkl")
    with open(temp_filename, "wb") as tmp_f:
        pickle.dump(msgs, tmp_f)
    return temp_filename


def get_size_file(file_path: str) -> int:
    with open(file_path, "rb") as f:
        size: int = f.seek(0, 2)
    return size
