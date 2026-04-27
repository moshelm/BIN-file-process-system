from pydantic import BaseModel
from enum import Enum

class StatusResult(str,Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
 
class ClientResponse(BaseModel):
    status:StatusResult