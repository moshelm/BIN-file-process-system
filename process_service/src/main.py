from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
import os 

from shared.logger_config import get_logger
from process_service.src.orchestrator import Orchestrator
from process_service.src.api.process_route import router as review_parsers
from process_service.src.api.gps_route import router as gps_msgs


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

app : FastAPI = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='0.0.0.0',port=8001)    
