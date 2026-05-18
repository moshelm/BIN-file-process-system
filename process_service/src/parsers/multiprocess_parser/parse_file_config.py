import mmap
from typing import List, Optional, Tuple

from process_service.src.parsers.pure_py_parser import SchemaBuilder
from shared.logger_config import get_logger

logger = get_logger(__name__)


class ArduPilotParser:
    def __init__(self) -> None:
        self.schema_builder = SchemaBuilder()

    def get_formats_and_length_messages(
        self,
        file_path: str,
    ) -> Optional[Tuple[List[str], List[int]]]:
        try:
            with open(file_path, "rb") as file:
                with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as binary_data:
                    schemas = self.schema_builder.extract_message_schemas(binary_data)

            formats: List[str] = [""] * 256
            lengths: List[int] = [0] * 256

            for schema in schemas:
                if schema is None:
                    continue
                formats[schema.message_id] = schema.struct_obj.format
                lengths[schema.message_id] = schema.length

            return formats, lengths
        except Exception:
            logger.exception("failed build format metadata")
            return None
