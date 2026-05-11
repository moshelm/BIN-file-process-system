from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from process_service.src.orchestrator import Orchestrator
from process_service.src.utils.file_handling import create_and_write_new_file_to_disc_async, remove_temp_file
from process_service.src.utils.helper import is_bin_file
from shared.logger_config import get_logger
from shared.schemas import ParseResult, ParseStatus

logger = get_logger(__name__)
router = APIRouter()


def get_manager(request: Request):
    return request.app.state.manager


def headers_handling(response: FileResponse, count: int, duration: str):
    response.headers["X-Total-Count"] = str(count)
    response.headers["X-Process-Duration"] = str(duration)


@router.post("/process_gps_messages", status_code=200)
async def process_bin_files(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    manager: Orchestrator = Depends(get_manager),
):
    try:
        if not is_bin_file(file.filename):
            raise HTTPException(status_code=401, detail="only .bin format")

        temp_file_path = str(Path(f"/tmp/{file.filename}"))

        await create_and_write_new_file_to_disc_async(file, temp_file_path)

        parse_gps_result: ParseResult = await manager.parser_gps_messages(temp_file_path)

        if parse_gps_result.status == ParseStatus.FAILED:
            raise HTTPException(status_code=500, detail="failed process this file")

        logger.info(
            f"File processed successfully | Total messages: {parse_gps_result.count} | Time: {parse_gps_result.duration}"
        )
        file_path = parse_gps_result.json_file_result_name

        response = None

        if file_path is None:
            response = parse_gps_result
        else:
            background_tasks.add_task(remove_temp_file, file_path)
            # background_tasks.add_task(remove_temp_file, temp_file_path)

            response = FileResponse(
                path=file_path,
                media_type="application/x-jsonlines",
                filename="gps_filtered_data.jsonl",
            )
        headers_handling(response, parse_gps_result.count, parse_gps_result.duration)
        return response

    except Exception as e:
        logger.error(f"Server failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="server failed")
