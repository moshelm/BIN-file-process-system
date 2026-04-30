import logging
import time

from redis import Redis

logger = logging.getLogger(__name__)


class RedisManager:

    RETRY_TIMES = 3

    def __init__(self, redis_uri: str):
        self.redis_uri = redis_uri
        self.redis = None
        self._connect()

    def _connect(self):
        for attempt in range(1, self.RETRY_TIMES + 1):
            try:
                self.redis = Redis.from_url(self.redis_uri)

                # This will raise if connection fails
                self.redis.ping()

                logger.info("Connected to Redis successfully")
                return

            except (ConnectionError, TimeoutError):
                logger.warning(
                    f"Redis connection failed (attempt {attempt}/{self.RETRY_TIMES})"
                )
                time.sleep(2)

        raise ConnectionError("Failed to connect to Redis after retries")
