import os


class Configuration:
    def __init__(self):
        self.bin_parser_uri = os.getenv("BIN_PARSER_URI", "http://localhost:8000/process")
        self.map_tile_url = os.getenv("MAP_TILE_URL", "https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png")
