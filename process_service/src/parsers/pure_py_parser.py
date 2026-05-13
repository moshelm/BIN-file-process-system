import mmap
import struct
import time
from dataclasses import dataclass
from typing import Dict,  List, Optional

from process_service.src.utils.helper import timer_calculate
from shared.logger_config import get_logger
from shared.schemas import ParseResult, ParseStatus

logger = get_logger(__name__)

@dataclass
class MessageSchema:
    type_id: int
    name: str
    length: int
    struct: struct.Struct
    columns: list[str]
    # אופטימיזציה: שמירת אינדקסים של עמודות שהן מחרוזות (bytes)
    string_indices: list[int] 

class PurePythonParser:
    FMT_STRUCT: struct.Struct = struct.Struct("<BB4s16s64s")
    MAGIC_HEADER: bytes = b"\xa3\x95"
    FMT_HEADER: bytes = b"\xa3\x95\x80"
    MINIMAL_FILE_SIZE = 100
    
    # מיפוי תווים של ArduPilot לפורמט Python Struct
    ARDU_TO_PYTHON_STRUCT: Dict[str, str] = {
        "a": "32s", "b": "b", "B": "B", "h": "h", "H": "H",
        "i": "i", "I": "I", "l": "i", "L": "i", "f": "f",
        "d": "d", "n": "4s", "N": "16s", "Z": "64s", "c": "h",
        "C": "H", "e": "i", "E": "I", "M": "B", "q": "q", "Q": "Q",
    }
    
    # תווים שמייצגים מחרוזות ודורשים decode
    STRING_FORMAT_CHARS = {"a", "n", "N", "Z"}

    def __init__(self) -> None:
        self.parser_name = "pure python parser"
        self.information = "use in bytes"
        self._struct_cache: Dict[str, tuple[struct.Struct, list[int]]] = {}

    def build_struct_from_format(self, decoded_format: str) -> tuple[struct.Struct, list[int]]:
        """
        בונה את ה-Struct ומזהה מראש אילו אינדקסים ב-Tuple שיתקבל הם מחרוזות.
        זה מונע את הצורך בבדיקות isinstance בתוך הלולאה הראשית.
        """
        if decoded_format in self._struct_cache:
            return self._struct_cache[decoded_format]

        try:
            python_format: List[str] = ["<"]
            string_indices: List[int] = []
            
            for i, char in enumerate(decoded_format):
                if char not in self.ARDU_TO_PYTHON_STRUCT:
                    logger.warning("Unsupported format char:%s", char)
                    raise ValueError(f"Unsupported format char: {char}")
                
                python_format.append(self.ARDU_TO_PYTHON_STRUCT[char])
                if char in self.STRING_FORMAT_CHARS:
                    string_indices.append(i)
                    
            struct_obj = struct.Struct("".join(python_format))
            result = (struct_obj, string_indices)
            self._struct_cache[decoded_format] = result
            return result
        except Exception:
            logger.error("serialize failed", extra={"failed_format": decoded_format})
            raise

    def extract_message_formats(self, binary_data: mmap.mmap) -> list[Optional[MessageSchema]]:
        formats: list[Optional[MessageSchema]] = [None] * 256
        search_offset: int = 0
        data_length: int = len(binary_data)

        while True:
            magic_pos: int = binary_data.find(self.FMT_HEADER, search_offset)
            if magic_pos == -1 or magic_pos + 89 >= data_length:
                break

            payload: bytes = binary_data[magic_pos + 3 : magic_pos + 89]
            type_id: int = payload[0]
            raw_format: str = payload[6:22].rstrip(b"\x00").decode("ascii", "ignore")
            
            try:
                # קבלת ה-Struct ואינדקסי המחרוזות
                struct_obj, str_indices = self.build_struct_from_format(raw_format)
                column_str = struct.Struct("64s").unpack_from(payload, 22)[0].rstrip(b"\x00").decode("ascii", "ignore")
                
                formats[type_id] = MessageSchema(
                    type_id=type_id,
                    name=payload[2:6].rstrip(b"\x00").decode("ascii", "ignore"),
                    length=payload[1],
                    struct=struct_obj,
                    string_indices=str_indices,
                    columns=[col for col in column_str.split(",") if col],
                )
            except Exception:
                pass

            search_offset = magic_pos + 89
        return formats

    def decode_messages(self, binary_data: mmap.mmap, formats: list[Optional[MessageSchema]], debug: bool = False, max_debug: int = 5) -> int:
        total_messages: int = 0
        data_size: int = len(binary_data)
        find_magic = binary_data.find
        current_pos: int = find_magic(self.MAGIC_HEADER, 0)
        
        # אופטימיזציה: קישור מקומי לפונקציית unpack_from חוסך חיפוש ב-Attribute Lookup
        unpack_from = struct.Struct.unpack_from

        while current_pos != -1:
            if current_pos + 3 >= data_size:
                break

            message_id: int = binary_data[current_pos + 2]
            fmt = formats[message_id] if message_id < 256 else None
            
            if fmt:
                message_end = current_pos + fmt.length
                if message_end <= data_size:
                    total_messages += 1
                    
                    # פריקה מהירה של הנתונים הגולמיים
                    unpacked_values = unpack_from(fmt.struct, binary_data, current_pos + 3)
                    
                    # פענוח מחרוזות רק אם ה-Schema אומרת שיש כאלו
                    if fmt.string_indices:
                        # הפיכה לרשימה רק לצורך מוטציה (שינוי ערכים)
                        vals_list = list(unpacked_values)
                        for idx in fmt.string_indices:
                            v = vals_list[idx]
                            # decode ו-rstrip רק על מה שאנחנו יודעים בוודאות שהוא bytes
                            vals_list[idx] = v.rstrip(b'\x00').decode('ascii', 'ignore')
                        processed_values = vals_list
                    else:
                        processed_values = unpacked_values

                    # הדפסה של 5 ההודעות הראשונות בלבד לבקשתך
                    if debug and total_messages <= max_debug:
                        print(f"\n[MSG {total_messages}] Type: {fmt.name} (ID:{message_id})")
                        # יצירת מילון רק לצרכי הדפסה ב-Debug
                        data_dict = dict(zip(fmt.columns, processed_values))
                        for key, val in data_dict.items():
                            print(f"    {key:20} = {val!r}")
                        if total_messages == max_debug:
                            print(f"\n--- ממשיך בעיבוד מהיר של שאר הקובץ (ללא הדפסה) ---")

                    current_pos = find_magic(self.MAGIC_HEADER, message_end)
                    continue

            current_pos = find_magic(self.MAGIC_HEADER, current_pos + 2)

        return total_messages

    def parse_file(self, file_path: str, specific_message: str | None = None, debug: bool = False) -> ParseResult:
        try:
            start_time: float = time.perf_counter()

            with open(file_path, "rb") as file:
                if file.seek(0, 2) == 0: raise ValueError("empty file")
                file.seek(0)
                with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as binary_data:
                    formats = self.extract_message_formats(binary_data)
                    total_messages = self.decode_messages(binary_data, formats, debug=debug, max_debug=190)

            return ParseResult(
                parser_name=self.parser_name,
                information=self.information,
                duration=timer_calculate(start_time),
                count=total_messages,
                status=ParseStatus.SUCCESS,
                file_path=file_path,
            )
        except Exception:
            logger.error("failed parse file")
            return ParseResult(self.parser_name, self.information, status=ParseStatus.FAILED, file_path=file_path)

if __name__ == '__main__':
    py = PurePythonParser()
    # הרץ עם debug=True כדי לראות את 5 ההודעות הראשונות מפוענחות
    result = py.parse_file('log_file_test_01.bin', debug=True)
    print(f"\nסיכום: {result.count} הודעות עובדו ב-{result.duration:.2f} שניות.")