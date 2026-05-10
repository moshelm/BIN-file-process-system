import struct
import mmap
import os
import time 
import tempfile

from process_service.src.utils.file_handling import remove_temp_file, write_to_temp_file_pickle, combine_files_zero_copy, get_size_file
from process_service.src.utils.helper import timer_calculate
from multiprocessing import Pool, cpu_count
from typing import Dict, List, Tuple, Optional, Any
from shared.schemas import ParseResult, ParseStatus
from shared.logger_config import get_logger
from process_service.src.parsers.multiprocess_parser.parse_file_config import ArduPilotParser

logger = get_logger(__name__)

CPU_AVAILABLE = min(1,cpu_count())

class ParseMultiprocess:
    CHUNK_SIZE: int = 16 * 1024 * 1024
    SAFETY_MARGIN: int = 1024
    MSG_HEADER_PREFIX: bytes = b'\xA3\x95'

    def __init__(self):
        self.parser_name = 'multiprocess parser'
        self.information = 'use in multi process'
        
    def parse_chunk(self,
        file_path:str,
        formats: List[Optional[str]],
        lens: List[int],
        start: int,
        end_original: int,
        temp_dir: str 
    ) -> Tuple[str, int, List[int]]:
        
        structs: List[Optional[struct.Struct]] = [
    struct.Struct(fmt) if fmt is not None else None
    for fmt in formats
]
        msgs: List[Tuple[int, Any]] = []
        wrong: List[int] = []

        with open(file_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                data_length: int = len(mm)
                end_chunk: int = min(end_original + self.SAFETY_MARGIN, data_length)
                index: int = start

                while index < end_chunk:
                    position: int = mm.find(self.MSG_HEADER_PREFIX, index, end_chunk)
                    if position == -1 or position + 3 >= end_chunk:
                        break

                    msg_type: int = mm[position + 2]

                    if msg_type == 0x80:
                        index = position + 89
                        continue

                    msg_len: int = lens[msg_type]
                    if msg_len == 0:
                        index = position + 2
                        continue

                    msg_end: int = position + msg_len

                    if msg_end > data_length:
                        wrong.append(msg_type)
                        break

                    struct_parser: Optional[struct.Struct] = structs[msg_type]

                    if struct_parser is not None and position < end_original:
                        msgs.append((msg_type, struct_parser.unpack_from(mm, position + 3)))

                    index = msg_end
        temp_filename = write_to_temp_file_pickle(temp_dir,msgs)
        
        return temp_filename, len(msgs), wrong
    
    def parse_file(self, file_path:str, formats, lens) -> Tuple[int, str]:
        try:
            size = get_size_file(file_path)
            temp_dir = tempfile.mkdtemp()
            start_time = time.perf_counter() 
            ranges: List[Tuple[str, List[Optional[str]], List[int], int, int, bytes, int, str]] = [
                (
                    file_path,
                    formats,  
                    lens, 
                    i, 
                    min(i + self.CHUNK_SIZE, size),
                    temp_dir 
                )
                for i in range(0, size, self.CHUNK_SIZE)
            ]
            
            with Pool(CPU_AVAILABLE) as p:
                results: List[Tuple[str, int, List[int]]] = p.starmap(self.parse_chunk, ranges)

            duration = timer_calculate(start_time)
            total_count = 0
            cut_messages: List[int] = []
            temp_files = []

            for tmp_file, count, cut in results:
                temp_files.append(tmp_file)
                total_count += count
                cut_messages.extend(cut)

            if cut_messages:
                logger.warning(f"cut messages: {len(cut_messages)}")
                
            combined_file_path = f"{file_path}.parsed.pkl"
            
            combine_files_zero_copy(combined_file_path,temp_files)
            os.rmdir(temp_dir)
                
            return duration , total_count, combined_file_path
            
        except Exception:
            logger.exception('parse file failed')
            return None, 0, "" 
                 

    def parse(self, file_path:str, ardupilot_parser: ArduPilotParser) -> ParseResult:
        
        formats, lens = ardupilot_parser.get_formats_and_length_messages(file_path)
        duration, total_count, combined_file = self.parse_file(file_path, formats, lens)
        remove_temp_file(combined_file)

        return ParseResult(
            parser_name=self.parser_name,
            information= self.information,
            duration=duration, 
            count=total_count+len(formats), 
            status=ParseStatus.SUCCESS, 
            file_path=combined_file
        )
