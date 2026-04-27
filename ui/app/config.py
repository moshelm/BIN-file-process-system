import os 


class Configuration():
    def __init__(self):
        self.bin_parser_uri = os.getenv('BIN_PARSER_URI',"http://localhost:8000/process")
        