import os 


class Configuration():
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL','redis://')