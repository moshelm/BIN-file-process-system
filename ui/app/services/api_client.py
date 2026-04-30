import logging 
import httpx
import json 
from pydantic import ValidationError
from shared.schemas import GPSMessages, GPSMessageResult

API_TIMEOUT = 30

class ApiClient:
    def __init__(self, base_url : str):
        self.base_url : str = base_url
        self.logger : logging.Logger = logging.getLogger(__name__)

    async def upload_file(self, local_filepath : str) -> GPSMessages:
        try:
            async with httpx.AsyncClient() as client:
                with open(local_filepath, "rb") as file:
                    response : httpx.Response = await client.post(
                        self.base_url,
                        files={
                            "file": (file.name, file, "application/octet-stream")
                        },
                        timeout=API_TIMEOUT,
                    )
                    response.raise_for_status()
                    content : str = response.content.decode("utf-8")
                    messages : GPSMessages | None = self.parse_and_validate(content)
                    
                    if messages is None:
                        self.logger.warning('there is no data from this url')
                        raise 

                    return messages
        except json.JSONDecodeError:
            self.logger.error("Failed parse jsonl to python object")
            raise
        except Exception as e:
            self.logger.error("Failed send to parser service. %s", str(e))
            raise
    
    def parse_and_validate(self, jsonl_data: str) -> GPSMessages | None:
        try:
            valid_messages = []
            for i, line in enumerate(jsonl_data.splitlines()) :
                if line.strip():
                    try:
                        data = json.loads(line)
                        msg_obj = GPSMessageResult.model_validate(data)
                        
                        valid_messages.append(msg_obj)
                    except json.JSONDecodeError:
                        self.logger.warning("Line %s: Invalid JSON format. Skipping.", i, extra={'line_error':line,'line_number':i})
                    except ValidationError as e:
                        self.logger.warning("Line %s: Data validation failed. Error: %s. Skipping.", i, e.json(), extra={'line_error':line,'line_number':i})
                    except Exception as e:
                        self.logger.warning("Line %s: Unexpected error: %s. Skipping.",i,e, extra={'line_error':line,'line_number':i})
            return GPSMessages(messages=valid_messages)
        except Exception :
            self.logger.error('failed parse data',exc_info=True)
            raise