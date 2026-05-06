from pydantic import BaseModel
from enum import Enum
from typing import Optional

class ParseStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending" 

class ParseResult(BaseModel):
    duration: Optional[float] = None
    count : int = 0
    status : ParseStatus = ParseStatus.PENDING
    file_path : Optional[str] = None
    json_file_result_name : Optional[str] = None

class GPSMessageResult(BaseModel):# check what this fields say
    TimeUS: int
    Status: int
    Lat: float
    Lng: float
    Alt: float
    Spd: float


class GPSMessages(BaseModel):
    messages: list[GPSMessageResult]
