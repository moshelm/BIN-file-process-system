import gc
import mmap
import struct
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from collections import namedtuple

from process_service.src.utils.helper import timer_calculate
from shared.logger_config import get_logger
from shared.schemas import ParseResult, ParseStatus

logger = get_logger(__name__)


@dataclass
class MessageSchema:
    message_id: int
    name: str
    length: int
    struct_obj: struct.Struct
    columns: list[str]
    string_indices: list[int]
    msg_class: Any


class SchemaBuilder:
    FMT_HEADER: bytes = b"\xa3\x95\x80"
    FMT_RECORD_SIZE: int = 86

    ARDU_TO_PYTHON_STRUCT: Dict[str, str] = {
        "a": "32s", "b": "b", "B": "B", "h": "h", "H": "H",
        "i": "i", "I": "I", "l": "i", "L": "i", "f": "f",
        "d": "d", "n": "4s", "N": "16s", "Z": "64s", "c": "h",
        "C": "H", "e": "i", "E": "I", "M": "B", "q": "q", "Q": "Q",
    }

    STRING_FORMAT_CHARS = {"a", "n", "N", "Z"}

    def __init__(self) -> None:
        self._struct_cache: Dict[str, tuple[struct.Struct, list[int]]] = {}

    def build_struct_from_format(self, decoded_format: str) -> tuple[struct.Struct, list[int]]:
        if decoded_format in self._struct_cache:
            return self._struct_cache[decoded_format]

        python_format: List[str] = ["<"]
        string_indices: List[int] = []

        for index, char in enumerate(decoded_format):
            if char not in self.ARDU_TO_PYTHON_STRUCT:
                logger.warning("Unsupported format char:%s", char)
                raise ValueError(f"Unsupported format char: {char}")

            python_format.append(self.ARDU_TO_PYTHON_STRUCT[char])
            if char in self.STRING_FORMAT_CHARS:
                string_indices.append(index)

        struct_obj = struct.Struct("".join(python_format))
        result = (struct_obj, string_indices)
        self._struct_cache[decoded_format] = result
        return result

    def extract_message_schemas(
        self,
        binary_data: mmap.mmap,
        specific_message: Optional[List[str]] = None,
    ) -> list[Optional[MessageSchema]]:
        schemas: list[Optional[MessageSchema]] = [None] * 256
        requested_names = set(specific_message or [])
        found_names: set[str] = set()

        search_offset: int = 0
        data_length: int = len(binary_data)

        while True:
            magic_pos: int = binary_data.find(self.FMT_HEADER, search_offset)
            if magic_pos == -1 or magic_pos + 3 + self.FMT_RECORD_SIZE > data_length:
                break

            payload: bytes = binary_data[magic_pos + 3 : magic_pos + 3 + self.FMT_RECORD_SIZE]
            message_id: int = payload[0]
            message_length: int = payload[1]
            message_name = payload[2:6].rstrip(b"\x00").decode("ascii", "ignore")
            raw_format = payload[6:22].rstrip(b"\x00").decode("ascii", "ignore")
            columns_raw = payload[22:86].rstrip(b"\x00").decode("ascii", "ignore")

            if requested_names and message_name not in requested_names:
                search_offset = magic_pos + 89
                continue

            try:
                struct_obj, string_indices = self.build_struct_from_format(raw_format)
                expected_length = struct_obj.size + 3
                if expected_length > message_length:
                    raise ValueError("message format size exceeds declared length")
                if not message_name.replace("_", "").isalnum():
                    raise ValueError("invalid message name")

                columns_list = [column for column in columns_raw.split(",") if column]
                message_class = namedtuple(f"Msg_{message_name}", columns_list, rename=True)

                schemas[message_id] = MessageSchema(
                    message_id=message_id,
                    name=message_name,
                    length=message_length,
                    struct_obj=struct_obj,
                    columns=columns_list,
                    string_indices=string_indices,
                    msg_class=message_class,
                )
                found_names.add(message_name)
            except Exception:
                logger.debug("skipped invalid FMT record at %s", magic_pos)

            search_offset = magic_pos + 89

        if requested_names and not requested_names.issubset(found_names):
            missing = requested_names - found_names
            raise ValueError(f"specific message not found: {', '.join(sorted(missing))}")

        return schemas


class BinaryDecoder:
    MAGIC_HEADER: bytes = b"\xa3\x95"

    @staticmethod
    def _unpack_message(binary_data: mmap.mmap, schema: MessageSchema, position: int) -> Any:
        unpacked_values = schema.struct_obj.unpack_from(binary_data, position + 3)
        if schema.string_indices:
            decoded_values = list(unpacked_values)
            for index in schema.string_indices:
                decoded_values[index] = decoded_values[index].rstrip(b"\x00").decode("ascii", "ignore")
            return schema.msg_class(*decoded_values)
        return schema.msg_class(*unpacked_values)

    def decode_messages(
        self,
        binary_data: mmap.mmap,
        schemas: list[Optional[MessageSchema]],
        debug: bool = False,
        max_debug: int = 5,
    ) -> list[Any]:
        data_length: int = len(binary_data)
        find_magic = binary_data.find
        current_pos = find_magic(self.MAGIC_HEADER, 0)
        messages: list[Any] = []

        gc.disable()
        try:
            while current_pos != -1:
                if current_pos + 3 >= data_length:
                    break

                message_id = binary_data[current_pos + 2]
                schema = schemas[message_id] if message_id < 256 else None

                if schema is None:
                    current_pos = find_magic(self.MAGIC_HEADER, current_pos + 2)
                    continue

                message_end = current_pos + schema.length
                if message_end > data_length:
                    break

                msg_obj = self._unpack_message(binary_data, schema, current_pos)
                messages.append(msg_obj)

                if debug and len(messages) <= max_debug:
                    print(f"\n[MSG {len(messages)}] Type: {schema.name} (ID:{message_id})")
                    print(msg_obj)
                    if len(messages) == max_debug:
                        print("\n--- continuing fast processing of the rest of the file (no printing) ---")

                current_pos = find_magic(self.MAGIC_HEADER, message_end)
        finally:
            gc.enable()

        return messages

    def count_chunk(
        self,
        binary_data: mmap.mmap,
        schemas: list[Optional[MessageSchema]],
        start: int,
        end_original: int,
        safety_margin: int,
    ) -> tuple[int, list[int]]:
        
        data_length: int = len(binary_data)
        end_chunk = min(end_original + safety_margin, data_length)
        find_magic = binary_data.find
        current_pos = find_magic(self.MAGIC_HEADER, start, end_chunk)

        success_count = 0
        wrong: list[int] = []
    
        while current_pos != -1 and current_pos + 3 < end_chunk:
            message_id = binary_data[current_pos + 2]
            if message_id == 0x80:
                if current_pos < end_original:
                    success_count += 1
                current_pos = find_magic(self.MAGIC_HEADER, current_pos + 89, end_chunk)
                continue

            schema = schemas[message_id] if message_id < 256 else None
            if schema is None:
                current_pos = find_magic(self.MAGIC_HEADER, current_pos + 2, end_chunk)
                continue

            message_end = current_pos + schema.length
            if message_end > data_length:
                wrong.append(message_id)
                break

            if current_pos < end_original:
                self._unpack_message(binary_data, schema, current_pos)
                success_count += 1

            current_pos = find_magic(self.MAGIC_HEADER, message_end, end_chunk)

        return success_count, wrong


class PurePythonParser:
    def __init__(self) -> None:
        self.parser_name = "pure python parser"
        self.information = "use in bytes"
        self.schema_builder = SchemaBuilder()
        self.binary_decoder = BinaryDecoder()

    def parse_file(
        self,
        file_path: str,
        specific_message: Optional[List[str]] = None,
        debug: bool = False,
    ) -> ParseResult:
        try:
            start_time = time.perf_counter()

            with open(file_path, "rb") as file:
                if file.seek(0, 2) == 0:
                    raise ValueError("empty file")
                file.seek(0)
                with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as binary_data:
                    schemas = self.schema_builder.extract_message_schemas(binary_data, specific_message)
                    messages = self.binary_decoder.decode_messages(binary_data, schemas, debug=debug)

            return ParseResult(
                parser_name=self.parser_name,
                information=self.information,
                duration=timer_calculate(start_time),
                count=len(messages),
                status=ParseStatus.SUCCESS,
                file_path=file_path,
            )
        except Exception as exc:
            logger.error("failed parse file: %s", exc)
            return ParseResult(
                parser_name=self.parser_name,
                information=self.information,
                status=ParseStatus.FAILED,
                file_path=file_path,
            )


class ChunkParser:
    def __init__(self) -> None:
        self.binary_decoder = BinaryDecoder()

    def parse_chunk(
        self,
        binary_data: mmap.mmap,
        schemas: list[Optional[MessageSchema]],
        start: int,
        end_original: int,
        safety_margin: int,
    ) -> tuple[int, list[int]]:
        return self.binary_decoder.count_chunk(binary_data, schemas, start, end_original, safety_margin)


if __name__ == '__main__':
    py = PurePythonParser()
    result = py.parse_file('log_file_test_01.bin', debug=True)
    print(f"\nSummary: {result.count} messages processed in {result.duration:.2f} seconds.")
