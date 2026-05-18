import mmap
import time
from multiprocessing import Pool, cpu_count
from typing import List, Optional, Tuple

from process_service.src.parsers.multiprocess_parser.parse_file_config import ArduPilotParser
from process_service.src.parsers.pure_py_parser import ChunkParser, SchemaBuilder
from process_service.src.utils.file_handling import get_size_file
from process_service.src.utils.helper import timer_calculate
from shared.logger_config import get_logger
from shared.schemas import ParseResult, ParseStatus

logger = get_logger(__name__)
CPU_AVAILABLE = max(1, cpu_count() - 1)


def _parse_chunk_worker(
    file_path: str,
    start: int,
    end_original: int,
    specific_message: Optional[List[str]],
    safety_margin: int,
) -> Tuple[int, List[int]]:
    try:
        with open(file_path, "rb") as file:
            with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as binary_data:
                schemas = SchemaBuilder().extract_message_schemas(binary_data, specific_message)
                return ChunkParser().parse_chunk(binary_data, schemas, start, end_original, safety_margin)
    except Exception:
        logger.exception("worker failed to parse chunk")
        return 0, []


class ParseMultiprocess:
    CHUNK_SIZE: int = 16 * 1024 * 1024
    SAFETY_MARGIN: int = 1024

    def __init__(self) -> None:
        self.parser_name = "multiprocess streaming parser"
        self.information = "use in multi process"

    def parse_file(
        self,
        file_path: str,
        specific_message: Optional[List[str]] = None,
    ) -> tuple[float, int, list[int]]:
        try:
            size = get_size_file(file_path)
            start_time = time.perf_counter()
            ranges = [
                (file_path, i, min(i + self.CHUNK_SIZE, size), specific_message, self.SAFETY_MARGIN)
                for i in range(0, size, self.CHUNK_SIZE)
            ]

            with Pool(CPU_AVAILABLE) as pool:
                results = pool.starmap(_parse_chunk_worker, ranges)

            total_count = sum(result[0] for result in results)
            cut_messages: list[int] = [wrong for result in results for wrong in result[1]]

            if cut_messages:
                logger.warning("worker chunk cut messages: %d", len(cut_messages))

            duration = timer_calculate(start_time)
            return duration, total_count, cut_messages

        except Exception:
            logger.exception("parse file failed")
            return 0.0, 0, []

    def parse(
        self,
        file_path: str,
        ardupilot_parser: ArduPilotParser,
        specific_message: Optional[List[str]] = None,
    ) -> ParseResult:
        try:
            _ = ardupilot_parser
            duration, total_count, cut_messages = self.parse_file(file_path, specific_message)
            if cut_messages:
                logger.warning("worker chunk cut messages: %d", len(cut_messages))

            return ParseResult(
                parser_name=self.parser_name,
                information=self.information,
                duration=duration,
                count=total_count,
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


if __name__ == '__main__':
    py = ParseMultiprocess()
    result = py.parse('log_file_test_01.bin', ArduPilotParser())
    print(f"\nSummary: {result.count} messages processed in {result.duration:.2f} seconds.")
