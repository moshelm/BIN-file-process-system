from pydantic import BaseModel

from shared.read_json import read_json_file


class ConfigJsonFile(BaseModel):
    redis_url: str


config_data = ConfigJsonFile(**(read_json_file("process-service/src/utils/config.json") or {}))
