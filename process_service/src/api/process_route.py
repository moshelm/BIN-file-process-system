from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from process_service.src.orchestrator import Orchestrator
from process_service.src.utils.file_handling import create_and_write_new_file_to_disc_async, remove_temp_file
from process_service.src.utils.helper import is_bin_file
from shared.logger_config import get_logger
from shared.schemas import ParseStatus

logger = get_logger(__name__)
router = APIRouter()


def get_manager(request: Request) -> Orchestrator:
    return request.app.state.manager


async def stream_parsed_objects(manager: Orchestrator, file_path: str) -> AsyncGenerator[str, None]:
    try:
        async for parse_file_result in manager.do_all_parsers(file_path):

            if parse_file_result is None or parse_file_result.status == ParseStatus.FAILED:
                logger.error("Failed to process file with one of the parsers")
                continue

            logger.info(f"File processed successfully | Total messages: {parse_file_result.count} \
                  | Time: {parse_file_result.duration}")
            res = f"{parse_file_result.model_dump_json()}\n"
            logger.info(res)
            yield res

    except Exception as e:
        logger.error(f"Error during streaming: {e}", exc_info=True)
    finally:
        remove_temp_file(file_path)
        logger.info(f"Temporary file {file_path} removed.")


@router.post("/process_file", status_code=200)
async def process_bin_files(
    file: UploadFile = File(...),
    manager: Orchestrator = Depends(get_manager),
) -> StreamingResponse:
    try:
        if not is_bin_file(file.filename):
            raise HTTPException(status_code=401, detail="only .bin format")

        temp_file_path = str(Path(f"/tmp/{file.filename}"))

        await create_and_write_new_file_to_disc_async(file, temp_file_path)

        return StreamingResponse(stream_parsed_objects(manager, temp_file_path), media_type="application/x-jsonlines")

    except Exception as e:
        logger.error(f"Server failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="server failed") from e


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
