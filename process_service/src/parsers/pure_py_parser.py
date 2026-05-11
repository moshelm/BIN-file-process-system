import struct
import time
from typing import Dict, List, Optional, Any
from shared.logger_config import get_logger
from shared.schemas import ParseResult, ParseStatus
from process_service.src.utils.helper import timer_calculate
import mmap
logger = get_logger(__name__)

class PurePythonParser:
    FMT_STRUCT: struct.Struct = struct.Struct('<BB4s16s64s')
    MAGIC_HEADER: bytes = b'\xA3\x95'
    FMT_HEADER: bytes = b'\xA3\x95\x80'
    MINIMAL_FILE_SIZE = 100
    ARDU_TO_PYTHON_STRUCT: Dict[str, str] = {
        'a': '32s', 'b': 'b', 'B': 'B', 'h': 'h', 'H': 'H',
        'i': 'i', 'I': 'I', 'l': 'i', 'L': 'i',
        'f': 'f', 'd': 'd', 'n': '4s', 'N': '16s', 'Z': '64s',
        'c': 'h', 'C': 'H', 'e': 'i', 'E': 'I', 'M': 'B',
        'q': 'q', 'Q': 'Q'
    }

    def __init__(self) -> None:
        self.parser_name = 'pure python parser'
        self.information = 'use in bytes'

    def build_struct_from_format(self, decoded_format: str) -> Optional[struct.Struct]:
        try:
            python_format: List[str] = ['<']
            for char in decoded_format:
                if char not in self.ARDU_TO_PYTHON_STRUCT:
                    logger.warning("Unsupported format char:%s", char, extra={'unknown_format': decoded_format})
                    raise ValueError(f"Unsupported format char: {char}")
                python_format.append(self.ARDU_TO_PYTHON_STRUCT[char])
            return struct.Struct(''.join(python_format))
        except Exception:
            logger.error('serialize failed', extra={'failed_format':  decoded_format})
            raise

    def extract_message_formats(self, binary_data: bytes) -> Dict[int, Dict[str, Any]]:
        try:
            formats: Dict[int, Dict[str, Any]] = {}
            search_offset: int = 0
            data_length: int = len(binary_data)

            while True:
                magic_pos: int = binary_data.find(self.FMT_HEADER, search_offset)

                if magic_pos == -1 or magic_pos + self.MINIMAL_FILE_SIZE >= data_length:
                    break

                start_msg_payload: int = magic_pos + 3
                end_msg_payload: int = start_msg_payload + 86
                payload: bytes = binary_data[start_msg_payload: end_msg_payload]
                
                type_id: int = payload[0]
                message_length: int = payload[1]
                raw_format: bytes = payload[6:22].rstrip(b'\x00').decode('ascii', 'ignore')
                try:
                    struct_obj: Optional[struct.Struct] = self.build_struct_from_format(raw_format)
                    formats[type_id] = {
                        'name': payload[2:6].rstrip(b'\x00').decode('ascii', 'ignore'),
                        "length": message_length,
                        "struct": struct_obj,
                        'columns': struct.Struct('64s').unpack_from(payload,22)[0].rstrip(b'\x00').decode('ascii', 'ignore')
                    }
                except Exception:
                    pass

                search_offset :int = magic_pos + 89

            return formats
        except Exception as e:
            logger.error(f'failed {str(e)}')
            raise

    def scan_message_offsets(
        self,
        binary_data: bytes,
        formats: Dict[int, Dict[str, Any]]
    ) -> List[List[int]]:
        try:
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
        except Exception:
            logger.error('scan messages offsets')

    def decode_messages(
        self,
        binary_data: bytes,
        offsets_by_message_id: List[List[int]],
        formats: Dict[int, Dict[str, Any]]
    ) -> int:
        try:
            total_messages: int = 0
            
            for message_id, offsets in enumerate(offsets_by_message_id):
                if not offsets:
                    continue

                format_info: Optional[Dict[str, struct.Struct|int|str ]] = formats.get(message_id)
                if not format_info:
                    continue

                unpack_from = format_info["struct"].unpack_from

                total_messages += len(offsets)
                
                for offset in offsets:
                    unpack_from(binary_data, offset)
                    
            return total_messages
        except Exception:
            logger.error('failed decoded')

    def parse_file(self, file_path: str, specific_message:str|None = None) -> Dict[str, Any]:
        try:
            start_time: float = time.perf_counter()
            
            with open(file_path, "rb") as file:
                with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as binary_data:
                    formats: Dict[int, Dict[str, Any]] = self.extract_message_formats(binary_data)
                    if specific_message:
                        specific_fmt = get_message_information_by_name(formats, specific_message)
                        formats = specific_fmt if specific_fmt is not None else formats

                    offsets: List[List[int]] = self.scan_message_offsets(binary_data, formats)
                    total_messages: int = self.decode_messages(binary_data, offsets, formats)

            duration: float = timer_calculate(start_time)

            return ParseResult(
                parser_name=self.parser_name,
                information= self.information,
                duration=duration, 
                count=total_messages, 
                status=ParseStatus.SUCCESS, 
                file_path=file_path
            )
        except Exception:
            logger.error('failed parse file')
            return ParseResult(
                parser_name=self.parser_name,
                information= self.information,
                status=ParseStatus.FAILED, 
                file_path=file_path
            )
def get_message_information_by_name(formats:dict[str,dict], name_message:str):
    try:
        for msg_id, info in formats.items():
            if info.get('name',None) == name_message:
                return {msg_id:info}
        return None
    except Exception:
        logger.error('failed get information by name')