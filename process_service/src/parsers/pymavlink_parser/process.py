from pymavlink import DFReader
from shared.logger_config import get_logger
from shared.schemas import ParseResult, ParseStatus
from process_service.src.utils.helper import timer_calculate
from process_service.src.utils.file_handling import close_temp_file, create_temporary_file, remove_temp_file
import time

from tempfile import _TemporaryFileWrapper
import json 


logger = get_logger(__name__)


class PymavlinkParser:
    GPS_INDEX = 'I'
    GPS_MSG = 'GPS'
    GPS_TYPE = 1

    def __init__(self):
        self.parser_name = 'pymavlink parser'
        self.information = 'use in mavlink'
        
    def parse_only_by_pymavlink(self,file_path:str)-> ParseResult:
        try:
            mav = DFReader.DFReader_binary(file_path)
            messages_number = mav._count
            start_time = time.perf_counter()
            
            while True:
                msg_raw = mav.recv_match(blocking=False)
                if msg_raw is None:
                    break
            
            duration = timer_calculate(start_time)

            return ParseResult(parser_name=self.parser_name,
            information= self.information,duration=duration, count=messages_number, status=ParseStatus.SUCCESS, file_path= file_path)
        except Exception as e :
            logger.error(f'failed parser. {str(e)}')
            return ParseResult(parser_name=self.parser_name,
            information= self.information,status=ParseStatus.FAILED, file_path= file_path)
        
        finally:
            if mav:
                mav.close()

    def parse_file_by_only_GPS_Messages(self, file_path:str,  gps_msg:str = GPS_MSG, gps_index: str = GPS_INDEX,gps_type:str = GPS_TYPE):
        try:
            temp_file : _TemporaryFileWrapper = create_temporary_file()
            start_time : float = time.perf_counter()
            mav : DFReader.DFReader_binary = DFReader.DFReader_binary(file_path)
            messages_number : int = 0
            messages = []
            app_msg = messages.append
            while True:
                msg_raw : DFReader.DFMessage = mav.recv_match(blocking=False, type=[gps_msg])
                if msg_raw is None:
                    break
                
                original_msg: dict = msg_raw.to_dict()
                if original_msg.get(gps_index, None) == gps_type:
                    app_msg(original_msg)
                    messages_number += 1
            for msg in messages:
                temp_file.write(json.dumps(msg) + "\n")
            duration = timer_calculate(start_time)
            
            return ParseResult(duration=duration, count=messages_number, status=ParseStatus.SUCCESS, file_path= file_path, json_file_result_name= temp_file.name)
        
        except Exception:
            remove_temp_file(temp_file.name)
            logger.error('failed parser',exc_info=True)
            return ParseResult( status=ParseStatus.FAILED, file_path= file_path)
        
        finally:
            close_temp_file(temp_file)
            if mav:
                mav.close()