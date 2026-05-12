import json
from pathlib import Path
from typing import Any

from shared.logger_config import get_logger

logger = get_logger(__name__)


def read_json_file(file_path: str) -> None | Any:
    try:
        path = Path(file_path).resolve()

        if not path.exists():
            logger.error(f"Error: Could not find config at {path.absolute()}")
            return None

        with path.open("r", encoding="utf-8") as file:
            return json.loads(file.read())

    except Exception:
        logger.error("failed read json file", exc_info=True, extra={"json_file": file_path})
        return None
