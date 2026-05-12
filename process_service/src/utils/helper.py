import time

from shared.logger_config import get_logger

logger = get_logger(__name__)


def is_bin_file(file_name: str | None) -> bool:
    try:
        if file_name is None:
            raise ValueError("file_name need to be str not None")
        return file_name.endswith(".bin")
    except Exception:
        logger.error("checking end file name failed", exc_info=True)
        return False


def timer_calculate(start_time: float) -> float:
    duration = time.perf_counter() - start_time
    logger.info(f"({int(duration//60)} min {duration%60:.2f} sec)")
    return round(duration, 2)
