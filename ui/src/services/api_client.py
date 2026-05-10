
import httpx
import json 
from collections.abc import AsyncIterator
from pydantic import ValidationError
from shared.schemas import GPSMessages, GPSMessageResult, ParseResult
from shared.logger_config import get_logger
import os 


API_TIMEOUT = 70

logger = get_logger(__name__)

class ApiClient:
    def __init__(self, base_url : str):
        self.base_url : str = base_url

    async def get_information_about_parsers(self, url:str, local_filepath : str) -> AsyncIterator[dict]:
        try:
            async with httpx.AsyncClient() as client:
                with open(local_filepath, 'rb') as file:
                    file_name = os.path.basename(file.name)
                    files = {"file": (file_name, file, "application/octet-stream")}
                    async with client.stream("POST",url,files=files, timeout=API_TIMEOUT) as response:
                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            try:
                                parse_info = ParseResult.model_validate_json(line)
                                yield parse_info.model_dump_json()
                            
                            except Exception as e:
                                logger.warning(f'no valid response from api. {str(e)}')

        except Exception as e :
            logger.error(f'failed review parsers. {str(e)}')


    async def upload_file_from_api(self, local_filepath : str) -> GPSMessages:
        try:
            async with httpx.AsyncClient() as client:
                with open(local_filepath, "rb") as file:
                    file_name = os.path.basename(file.name)
                    response : httpx.Response = await client.post(
                        self.base_url,
                        files={
                            "file": (file_name, file, "application/octet-stream")
                        },
                        timeout=API_TIMEOUT,
                    )
                    response.raise_for_status()
                    content : str = response.content.decode("utf-8")
                    messages : GPSMessages | None = self.parse_and_validate(content)
                    
                    if messages is None:
                        logger.warning('there is no data from this url')
                        raise 

                    return messages
        except json.JSONDecodeError:
            logger.error("Failed parse jsonl to python object")
            raise
        except Exception as e:
            logger.error("Failed send to parser service. %s", str(e))
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
                        logger.warning("Line %s: Invalid JSON format. Skipping.", i, extra={'line_error':line,'line_number':i})
                    except ValidationError as e:
                        logger.warning("Line %s: Data validation failed. Error: %s. Skipping.", i, e.json(), extra={'line_error':line,'line_number':i})
                    except Exception as e:
                        logger.warning("Line %s: Unexpected error: %s. Skipping.",i,e, extra={'line_error':line,'line_number':i})
            return GPSMessages(messages=valid_messages)
        except Exception :
            logger.error('failed parse data',exc_info=True)
            raise