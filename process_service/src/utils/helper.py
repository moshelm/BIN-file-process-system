import os 
from shared.logger_config import get_logger
import time 


logger = get_logger(__name__)


def is_bin_file(file_name: str) -> bool:
    try:
        if file_name.endswith(".bin"):
            return True
        return False
    except Exception:
        logger.error("checking end file name failed", exc_info=True)
        return False
    
def timer_calculate(start_time:float):
        duration = time.perf_counter() - start_time
        logger.info(f"({int(duration//60)} min {duration%60:.2f} sec)")
        return duration

