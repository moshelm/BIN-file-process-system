import mmap
import struct
from typing import Any, Dict, List, Tuple

from shared.logger_config import get_logger

logger = get_logger(__name__)


class ArduPilotParser:
    FMT_STRUCT: struct.Struct = struct.Struct("<BB4s16s64s")
    FMT_HEADER: bytes = b"\xa3\x95\x80"
    ARDU_TO_PYTHON_STRUCT: Dict[str, str] = {
        "a": "32s",
        "b": "b",
        "B": "B",
        "h": "h",
        "H": "H",
        "i": "i",
        "I": "I",
        "l": "i",
        "L": "i",
        "f": "f",
        "d": "d",
        "n": "4s",
        "N": "16s",
        "Z": "64s",
        "c": "h",
        "C": "H",
        "e": "i",
        "E": "I",
        "M": "B",
        "q": "q",
        "Q": "Q",
    }

    def __init__(self) -> None:
        pass

    def serialize_to_python_format(self, format_str: str) -> str:
        try:
            python_format: List[str] = ["<"]
            for char in format_str:
                if char not in self.ARDU_TO_PYTHON_STRUCT:
                    logger.warning("Unsupported format char:%s", char, extra={"unknown_format": format_str})
                    raise ValueError(f"Unsupported format char: {char}")
                python_format.append(self.ARDU_TO_PYTHON_STRUCT[char])
            return "".join(python_format)
        except Exception:
            logger.error("serialize failed", extra={"failed_format": format_str})
            raise

    def scan_fmt_messages(self, file_path: str) -> Dict[int, Dict[str, Any]]:
        fmt_dict: Dict[int, Dict[str, Any]] = {}
        try:
            with open(file_path, "rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    position: int = 0
                    size: int = len(mm)

                    while True:
                        position = mm.find(self.FMT_HEADER, position)
                        if position == -1:
                            break
                        start: int = position + 3
                        end: int = start + 86
                        if end > size:
                            break
                        payload: bytes = mm[start:end]
                        result: Tuple[Any, ...] = self.FMT_STRUCT.unpack(payload)

                        msg_id: int = result[0]
                        length: int = result[1]
                        name: str = result[2].rstrip(b"\x00").decode("ascii", "ignore")
                        format_str: str = result[3].rstrip(b"\x00").decode("ascii", "ignore")
                        columns: str = result[4].rstrip(b"\x00").decode("ascii", "ignore")

                        try:
                            py_fmt: str = self.serialize_to_python_format(format_str)
                            expected_len: int = struct.calcsize(py_fmt) + 3
                        except Exception:
                            logger.error(f"failed msg_id:{msg_id}, name:{name},fmt:{format_str}")
                            position += 1
                            continue

                        if expected_len > length:
                            position += 1
                            continue

                        if not name.replace("_", "").isalnum():
                            position += 1
                            continue

                        fmt_dict[msg_id] = {
                            "length": length,
                            "name": name,
                            "format": format_str,
                            "columns": columns.split(","),
                            "python_format": py_fmt,
                        }
                        position += 89
            return fmt_dict
        except Exception:
            logger.exception("failed scan fmt messages")
            return {}

    def _prepare_formats_and_lens(self, fmt_dict: dict[int, dict]) -> Tuple[List[str], List[int]] | None:
        try:
            formats: List[str] = [''] * 256
            lens: List[int] = [0] * 256
            for msg_id, info in fmt_dict.items():
                lens[msg_id] = info["length"]
                if info.get("python_format"):
                    formats[msg_id] = info["python_format"]

            return formats, lens
        except Exception:
            logger.error("failed analyze formats and lans")
            return None

    def get_formats_and_length_messages(self, file_path: str) -> Tuple[List[str], List[int]] | None:
        try:
            fmt_dict = self.scan_fmt_messages(file_path)
            return self._prepare_formats_and_lens(fmt_dict)
        except Exception:
            logger.error("failed get configuration of file messages")
            return None
