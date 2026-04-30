import json
import logging
import os
import flet as ft
import httpx

class PickerUploadFiles:
    def __init__(self, page: ft.Page, target_url_parser_service: str):
        self.logger = logging.getLogger(__name__)
        self.page = page
        self.parser_service_url = target_url_parser_service
        self.file_picker: ft.FilePicker = ft.FilePicker(on_upload=self.on_upload_progress)

        self.picked_files: list[ft.FilePickerFile] = []
        self.prog_bars: dict[str, ft.ProgressRing] = {}
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

    async def on_upload_progress(self, e: ft.FilePickerUploadEvent):
        self.prog_bars[e.file_name].value = e.progress
        self.page.update()

        # כשהקובץ סיים להעלות לתיקייה המקומית ב-Docker
        if e.progress == 1.0:
            # כאן אנחנו יוצרים את הנתיב לקובץ שנמצא כעת בתוך ה-Docker
            local_filepath = os.path.join(os.getcwd(), "/tmp/uploads", e.file_name)

            try:
                self.logger.info("File %s uploaded locally, sending to parser...", e.file_name)
                async with httpx.AsyncClient() as client:
                    with open(local_filepath, "rb") as f:
                        response = await client.post(
                            self.parser_service_url,
                            files={"file": (e.file_name, f, "application/octet-stream")},
                            timeout=30,
                        )
                        response.raise_for_status()
                        content = response.content.decode("utf-8")
                        raw_data = parse_jsonl(content)

                        if self.callback:
                            self.callback(raw_data)

            except json.JSONDecodeError:
                self.logger.error("Failed parse jsonl to python object")
                raise
            except Exception as ex:
                self.logger.error("Failed send to parser service. %s", str(ex))
                raise
            finally:
                self.upload_button.disabled = False
                self.page.update()

                if os.path.exists(local_filepath):
                    os.remove(local_filepath)
                    self.logger.info("Cleaned up temporary file: %s", local_filepath)

    async def handle_files_pick(self, e: ft.Event[ft.Button]) -> None:
        try:
            files = await self.file_picker.pick_files(allow_multiple=True)

            log_files = [{"name": f.name, "size": f.size} for f in files]
            self.logger.info("Picked files:%s", log_files)
            self.picked_files = files
            if not files:
                self.logger.warning("there is no files in this upload order")
            # update progress bars
            self.upload_button.disabled = len(files) == 0
            self.prog_bars.clear()
            self.upload_progress.controls.clear()
            for f in files:
                prog = ft.ProgressRing(value=0, bgcolor="#eeeeee", width=20, height=20)
                self.prog_bars[f.name] = prog
                self.upload_progress.controls.append(ft.Row([prog, ft.Text(f.name)]))
            self.page.update()
        except Exception:
            self.logger.error("failed pick files", exc_info=True)

    async def handle_file_upload(self, e: ft.Event[ft.Button]):
        try:
            # initialize for upload only once
            self.upload_button.disabled = True
            import os

            os.makedirs("/tmp/uploads", exist_ok=True)
            upload_files = []
            for file in self.picked_files:
                upload_url = self.page.get_upload_url(file.name, 60)
                upload_files.append(ft.FilePickerUploadFile(upload_url=upload_url, name=file.name))

            await self.file_picker.upload(upload_files)
        except Exception:
            self.logger.error("failed upload", exc_info=True)

    def process_picker_and_upload_files(self, callback):
        self.callback = callback
        self.page.add(
            ft.SafeArea(
                content=ft.Column(
                    controls=[
                        self.button_pick,
                        self.upload_progress,
                        self.upload_button,
                    ],
                ),
            )
        )


def parse_jsonl(jsonl_data: str):
    try:
        return [json.loads(line) for line in jsonl_data.splitlines() if line.strip()]
    except json.JSONDecodeError:
        raise
