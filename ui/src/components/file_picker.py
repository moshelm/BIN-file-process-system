import json
import os
from typing import Callable

import flet as ft

from shared.logger_config import get_logger
from shared.schemas import GPSMessages

logger = get_logger(__name__)

class PickerUploadFiles:
    def __init__(self, page: ft.Page): 
        self.page : ft.Page = page

        self.file_picker: ft.FilePicker = ft.FilePicker()

        self.picked_files: list[ft.FilePickerFile] = []
        self.progress_circle_view: dict[str, ft.ProgressRing] = {}
        self.callback = None

        self.button_pick = ft.Button(
            content="Select files...",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self.handle_files_pick,
        )
        self.upload_progress = ft.Column()
        self.upload_button = ft.Button(
            content="Upload",
            icon=ft.Icons.UPLOAD,
            on_click=self.handle_file_upload,
            disabled=True,
        )
        
    def get_callback_function(self, callback : Callable[[str],GPSMessages]):
        self.callback : Callable[[str],GPSMessages] = callback

    async def on_upload_progress(self, e: ft.FilePickerUploadEvent):
        try:
            self.progress_circle_view[e.file_name].value = e.progress
            self.page.update()
            local_filepath = os.path.join(os.getcwd(), "/tmp/uploads", e.file_name)
            if e.progress == 1.0:
                logger.info(
                    "File %s uploaded locally, sending to parser...", e.file_name
                )
                await self.callback(local_filepath)

        except json.JSONDecodeError:
            logger.error("Failed parse jsonl to python object")
            raise
        except Exception as ex:
            logger.error("Failed send to parser service. %s", str(ex))
            raise
        finally:
            self.upload_button.disabled = False
            self.page.update()

            if os.path.exists(local_filepath):
                os.remove(local_filepath)
                logger.info("Cleaned up temporary file: %s", local_filepath)

    async def handle_files_pick(self, e: ft.Event[ft.Button]) -> None:
        try:
            files : list[ft.FilePickerFile]= await self.file_picker.pick_files(allow_multiple=False)

            log_files : list[dict[str, str|int]] = [{"name": file.name, "size": file.size} for file in files]
            logger.info("Picked files:%s", log_files)
            
            self.picked_files = files
            if not files:
                logger.warning("there is no files in this upload order")
            
            self.upload_button.disabled = len(files) == 0
            self.progress_circle_view.clear()
            self.upload_progress.controls.clear()
            for f in files:
                progress_ring = ft.ProgressRing(value=0, bgcolor="#eeeeee", width=20, height=20)
                self.progress_circle_view[f.name] = progress_ring
                self.upload_progress.controls.append(ft.Row([progress_ring, ft.Text(f.name)]))
            self.page.update()
        except Exception:
            logger.error("failed pick files", exc_info=True)

    async def handle_file_upload(self, e: ft.Event[ft.Button]):
        try:
            self.upload_button.disabled = True
            os.makedirs("/tmp/uploads", exist_ok=True)
            upload_files = []
            for file in self.picked_files:
                upload_url = self.page.get_upload_url(file.name, 60)
                upload_files.append(
                    ft.FilePickerUploadFile(upload_url=upload_url, name=file.name)
                )

            self.file_picker.on_upload= self.on_upload_progress
            await self.file_picker.upload(upload_files)
        except Exception:
            logger.error("failed upload", exc_info=True)

    def create_picker_file_view(self):
        return ft.Column(
            controls=[
                self.button_pick,
                self.upload_progress,
                self.upload_button,
            ],
        )
