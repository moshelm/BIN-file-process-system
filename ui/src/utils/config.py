from pydantic import BaseModel

from shared.read_json import read_json_file


class ConfigJsonFile(BaseModel):
    bin_parser_gps: str = "http://localhost:8000/process"
    bin_parsers_review: str = "http://parser-service:8001/process_file"
    map_tile_url: str = "https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"


config_data = ConfigJsonFile(**(read_json_file("ui/src/utils/config.json") or {}))
