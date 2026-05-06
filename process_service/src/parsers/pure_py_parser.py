import struct
import time
from typing import Dict, List, Optional, Any
from shared.logger_config import get_logger
from shared.schemas import ParseResult, ParseStatus
from process_service.src.utils.helper import timer_calculate

logger = get_logger(__name__)

class PurePythonParser:
    MAGIC_HEADER: bytes = b'\xA3\x95'

    FORMAT_MAP: Dict[str, str] = {
        'a': '32s', 'b': 'b', 'B': 'B', 'h': 'h', 'H': 'H',
        'i': 'i', 'I': 'I', 'l': 'i', 'L': 'i',
        'f': 'f', 'd': 'd', 'n': '4s', 'N': '16s', 'Z': '64s',
        'c': 'h', 'C': 'H', 'e': 'i', 'E': 'I', 'M': 'B',
        'q': 'q', 'Q': 'Q'
    }

    def __init__(self) -> None:
        pass

    def build_struct_from_format(self, format_bytes: bytes) -> Optional[struct.Struct]:
        struct_format: str = '<'

        decoded_format: str = format_bytes.rstrip(b'\x00').decode('ascii', 'ignore')

        for format_char in decoded_format:
            if format_char not in self.FORMAT_MAP:
                return None
            struct_format += self.FORMAT_MAP[format_char]

        return struct.Struct(struct_format)

    def extract_message_formats(self, binary_data: bytes) -> Dict[int, Dict[str, Any]]:
        formats: Dict[int, Dict[str, Any]] = {}
        search_offset: int = 0
        data_length: int = len(binary_data)

        while True:
            magic_pos: int = binary_data.find(self.MAGIC_HEADER, search_offset)

            if magic_pos == -1 or magic_pos + 100 >= data_length:
                break

            message_id: int = binary_data[magic_pos + 2]

            if message_id == 128:
                payload: bytes = binary_data[magic_pos + 3: magic_pos + 3 + 86]

                try:
                    type_id: int = payload[0]
                    message_length: int = payload[1]
                    raw_format: bytes = payload[6:22].strip(b'\x00')

                    struct_obj: Optional[struct.Struct] = self.build_struct_from_format(raw_format)

                    if struct_obj:
                        formats[type_id] = {
                            "length": message_length,
                            "struct": struct_obj
                        }
                except Exception:
                    pass

            search_offset :int = magic_pos + 2

        return formats

    def scan_message_offsets(
        self,
        binary_data: bytes,
        formats: Dict[int, Dict[str, Any]]
    ) -> List[List[int]]:

        message_lengths: List[int] = [0] * 256

        for msg_id, info in formats.items():
            message_lengths[msg_id] = info["length"]

        offsets_by_message_id: List[List[int]] = [[] for _ in range(256)]

        data_size: int = len(binary_data)
        find_magic = binary_data.find
        current_pos: int = find_magic(self.MAGIC_HEADER, 0)

        while current_pos != -1:
            if current_pos + 3 >= data_size:
                break

            message_id: int = binary_data[current_pos + 2]
            message_length: int = message_lengths[message_id]

            if message_length:
                message_end: int = current_pos + message_length

                if message_end > data_size:
                    break

                offsets_by_message_id[message_id].append(current_pos + 3)
                current_pos : int = find_magic(self.MAGIC_HEADER, message_end)
            else:
                current_pos : int = find_magic(self.MAGIC_HEADER, current_pos + 2)

        return offsets_by_message_id

    def decode_messages(
        self,
        binary_data: bytes,
        offsets_by_message_id: List[List[int]],
        formats: Dict[int, Dict[str, Any]]
    ) -> int:

        total_messages: int = 0

        for message_id, offsets in enumerate(offsets_by_message_id):
            if not offsets:
                continue

            format_info: Optional[Dict[str, Any]] = formats.get(message_id)
            if not format_info:
                continue

            unpack_from = format_info["struct"].unpack_from

            total_messages += len(offsets)

            for offset in offsets:
                unpack_from(binary_data, offset)

        return total_messages

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        start_time: float = time.perf_counter()

        with open(file_path, "rb") as file:
            binary_data: bytes = file.read()

        formats: Dict[int, Dict[str, Any]] = self.extract_message_formats(binary_data)
        offsets: List[List[int]] = self.scan_message_offsets(binary_data, formats)
        total_messages: int = self.decode_messages(binary_data, offsets, formats)

        duration: float = timer_calculate(start_time)

        return ParseResult(
            duration=duration, 
            count=total_messages, 
            status=ParseStatus.SUCCESS, 
            file_path=file_path
        )
    
# if __name__ == "__main__":
#     parser = PurePythonParser()

#     file_path: str = "log_file_test_01.bin"

#     print("🚀 SAFE & FAST PARSER")

#     result: Dict[str, Any] = parser.parse_file(file_path)

#     print(f"✅ messages: {result['messages']} | time: {result['time']} sec")