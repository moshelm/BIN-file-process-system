from enum import Enum

from pydantic import BaseModel


class StatusResult(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ClientResponse(BaseModel):
    status: StatusResult
