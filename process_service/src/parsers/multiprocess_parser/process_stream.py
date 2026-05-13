import mmap
import struct
import time
from multiprocessing import Pool, cpu_count
from typing import List, Optional, Tuple

from process_service.src.parsers.multiprocess_parser.parse_file_config import ArduPilotParser
from process_service.src.utils.file_handling import get_size_file, remove_temp_file
from process_service.src.utils.helper import timer_calculate
from shared.logger_config import get_logger
from shared.schemas import ParseResult, ParseStatus

logger = get_logger(__name__)

CPU_AVAILABLE = max(1, cpu_count() - 1)


class ParseMultiprocess:
    CHUNK_SIZE: int = 16 * 1024 * 1024
    SAFETY_MARGIN: int = 1024
    MSG_HEADER_PREFIX: bytes = b"\xa3\x95"

    def __init__(self) -> None:
        self.parser_name = "multiprocess streaming parser"
        self.information = "use in multi process"

    def parse_chunk(
        self,
        file_path: str,
        formats: List[Optional[str]],
        lens: List[int],
        start: int,
        end_original: int,
    ) -> Tuple[int, List[int]]:

        structs: List[Optional[struct.Struct]] = [struct.Struct(fmt) if fmt else None for fmt in formats]
        wrong: List[int] = []
        count: int = 0

        with open(file_path, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                data_length: int = len(mm)
                end_chunk: int = min(end_original + self.SAFETY_MARGIN, data_length)
                index: int = start
                c =190
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
                        struct_parser.unpack_from(mm, position + 3)
                        count += 1

                    index = msg_end

        return count, wrong

    def parse_file(self, file_path: str, formats: list[str], lens: list[int]) -> tuple[float, int, str]:
        try:
            size = get_size_file(file_path)
            start_time = time.perf_counter()
            ranges: List[Tuple[str, List[str], List[int], int, int, str]] = [
                (file_path, formats, lens, i, min(i + self.CHUNK_SIZE, size))
                for i in range(0, size, self.CHUNK_SIZE)
            ]

            with Pool(CPU_AVAILABLE) as p:
                results: List[Tuple[int, List[int]]] = p.starmap(self.parse_chunk, ranges)

            duration = timer_calculate(start_time)
            total_count = 0
            cut_messages: List[int] = []

            for count, cut in results:
                total_count += count
                cut_messages.extend(cut)

            if cut_messages:
                logger.warning(f"cut messages: {len(cut_messages)}")

            return duration, total_count, ""

        except Exception:
            logger.exception("parse file failed")
            return 0.0, 0, ""

    def parse(self, file_path: str, ardupilot_parser: ArduPilotParser) -> ParseResult:
        try:
            formats, lens = ardupilot_parser.get_formats_and_length_messages(file_path) or (None, None)
            if formats is None or lens is None:
                raise ValueError("some args are None")

            duration, total_count, combined_file = self.parse_file(file_path, formats, lens)
            if combined_file:
                remove_temp_file(combined_file)

            return ParseResult(
                parser_name=self.parser_name,
                information=self.information,
                duration=duration,
                count=total_count + sum_msgs_formats(formats),
                status=ParseStatus.SUCCESS,
                file_path=file_path,
            )
        except Exception:
            logger.error("failed parse file")
            return ParseResult(
                parser_name=self.parser_name,
                information=self.information,
                status=ParseStatus.FAILED,
                file_path=file_path,
            )


def sum_msgs_formats(formats: list[str]) -> int:
    return len([fmt for fmt in formats if fmt ])

if __name__=='__main__':
    py = ParseMultiprocess()
    print(py.parse('log_file_test_01.bin',ArduPilotParser()))