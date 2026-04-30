import logging
import os

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse
from orchestrator import Orchestrator
from schemas import ClientResponse, StatusResult

logger = logging.getLogger(__name__)
router = APIRouter()


def get_manager(request: Request):
    return request.app.state.manager


def remove_temp_file(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logger.info(f"Deleted temp file: {path}")
    except Exception as e:
        logger.error(f"Failed to delete temp file {path}: {e}")


@router.post("/process", status_code=200)
async def process_bin_files(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    manager: Orchestrator = Depends(get_manager),
):
    try:
        if not is_bin_file(file.filename):
            raise HTTPException(status_code=401, detail="only .bin format")

        result = await manager.process(file.file.fileno())

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        file_path = result.get("file_path")
        count = result.get("count", 0)
        duration = result.get("duration_sec", "unknown")

        logger.info(
            f"File processed successfully | Total messages: {count} | Time: {duration}"
        )

        background_tasks.add_task(remove_temp_file, file_path)

        response = FileResponse(
            path=file_path,
            media_type="application/x-jsonlines",
            filename="gps_filtered_data.jsonl",
        )

        # Headers
        response.headers["X-Total-Count"] = str(count)
        response.headers["X-Process-Duration"] = str(duration)

        return response
    except Exception as e:
        logger.error(f"Server failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"server failed: {str(e)}")

@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/result/{task_id}", status_code=200)
async def get_task_id(task_id: int):
    pass


def is_bin_file(file_name: str):
    try:
        if file_name.endswith(".bin"):
            return True
        return False
    except Exception:
        logger.error("checking end file name failed", exc_info=True)
        return False
