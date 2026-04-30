from pydantic import BaseModel


class MessageBin(BaseModel):
    pass


class GPSMessageResult(BaseModel):
    TimeUS: int
    Status: int
    Lat: float
    Lng: float
    Alt: float
    Spd: float


class GPSMessages(BaseModel):
    messages: list[GPSMessageResult]
