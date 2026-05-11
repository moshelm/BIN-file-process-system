import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from process_service.src.api.gps_route import router as gps_msgs
from process_service.src.api.process_route import router as review_parsers
from process_service.src.orchestrator import Orchestrator
from shared.logger_config import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        manager = Orchestrator()
        app.state.manager = manager

        yield

        logger.info("server shutdown")

    except Exception:
        logger.error("API server failed ", exc_info=True)


if __name__ == "__main__":
    PORT = int(os.getenv("PROCESS_SERVICE_PORT", "8001"))
    HOST = os.getenv("PROCESS_SERVICE_HOST", "0.0.0.0")

    app: FastAPI = FastAPI(lifespan=lifespan)
    app.include_router(review_parsers)
    app.include_router(gps_msgs)
    uvicorn.run(app, host=HOST, port=PORT)
