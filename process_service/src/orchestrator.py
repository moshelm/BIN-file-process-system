import asyncio
from shared.logger_config import get_logger
from shared.schemas import ParseResult
from process_service.src.parsers.pymavlink_parser.process import PymavlinkParser
from process_service.src.parsers.multiprocess_parser.multi_process import ParseMultiprocess
from process_service.src.parsers.pure_py_parser import PurePythonParser

logger = get_logger(__name__)

class Orchestrator:
    def __init__(self):
        self.pymavlink_parser = PymavlinkParser()
        self.multiprocess_parser = ParseMultiprocess()
        self.python_parser = PurePythonParser()

    async def parser_gps_messages(self, file_path:str) -> ParseResult:
        return await asyncio.to_thread(self.pymavlink_parser.parse_file_by_only_GPS_Messages, file_path)
    
    async def parser_pure_python(self, file_path:str) -> ParseResult:
        return await asyncio.to_thread(self.python_parser.parse_file, file_path)

    async def parser_all_file_mavlink(self, file_path:str) -> ParseResult:
        return await asyncio.to_thread(self.pymavlink_parser.parse_only_by_pymavlink, file_path)
    
    async def parser_file_multiprocess(self, file_path:str):
        return await asyncio.to_thread(self.multiprocess_parser.parse, file_path)
    
 
