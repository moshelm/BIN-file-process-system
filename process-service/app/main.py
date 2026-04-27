from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import Configuration
from .routes import router
import logging 
from shared.redis_connection import RedisManager
from .orchestrator import Orchestrator


def  setup_logging():
    logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

@asynccontextmanager
async def lifespan(app:FastAPI):
    setup_logging()
    logger = logging.getLogger(__name__)
    try:
        config = Configuration()
        redis = RedisManager(config.redis_url)
        manager = Orchestrator()
        app.state.manager = manager
        yield
        logger.info('server shutdown')
    except Exception:
        logger.error('API server failed',exc_info=True)

app = FastAPI(lifespan=lifespan)
app.include_router(router)