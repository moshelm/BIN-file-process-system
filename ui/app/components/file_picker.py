# """ the program work only on  running in desktop not web for running 
# flet run not use in --web
# """
from dataclasses import dataclass, field

import flet as ft
import json

@dataclass
class State:
    file_picker: ft.FilePicker | None = None
    picked_files: list[ft.FilePickerFile] = field(default_factory=list)


class PickerUploadFiles():
    def __init__(self, page: ft.Page, target_url_parser_service: str, state:State = State()):
        self.state = state
        self.page = page 
        self.parser_service_url = target_url_parser_service

    def process_picker_and_upload_files(self, callback):
        prog_bars: dict[str, ft.ProgressRing] = {}

        def on_upload_progress(e: ft.FilePickerUploadEvent):
            prog_bars[e.file_name].value = e.progress

        async def handle_files_pick(e: ft.Event[ft.Button]):
            self.state.file_picker = ft.FilePicker(on_upload=on_upload_progress)
            files = await self.state.file_picker.pick_files(allow_multiple=True)
            print("Picked files:", files)
            self.state.picked_files = files

            # update progress bars
            upload_button.disabled = len(files) == 0
            prog_bars.clear()
            upload_progress.controls.clear()
            for f in files:
                prog = ft.ProgressRing(value=0, bgcolor="#eeeeee", width=20, height=20)
                prog_bars[f.name] = prog
                upload_progress.controls.append(ft.Row([prog, ft.Text(f.name)]))
                self.page.update()
        async def handle_file_upload(e: ft.Event[ft.Button]):
            upload_button.disabled = True
            import httpx
            for file in self.state.picked_files:
                async with httpx.AsyncClient() as client:
                    with open(file.path, "rb") as f:
                        response = await client.post(
                            self.parser_service_url,
                            files={"file": (file.name, f, "application/octet-stream")}
                            ,timeout=15
                        )
                        response.raise_for_status()
                        content = response.content.decode("utf-8")
                        raw_data =  [
                            json.loads(line)
                            for line in content.splitlines()
                            if line.strip()
                        ]

                        callback(raw_data) 

            upload_button.disabled = False
            upload_button.update()

        self.page.add(
            ft.SafeArea(
                content=ft.Column(
                    controls=[
                        ft.Button(
                            content="Select files...",
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=handle_files_pick,
                        ),
                        upload_progress := ft.Column(),
                        upload_button := ft.Button(
                            content="Upload",
                            icon=ft.Icons.UPLOAD,
                            on_click=handle_file_upload,
                            disabled=True,
                        ),
                    ],
                ),
            )
        )
def parse_jsonl(self):
        """פונקציה פנימית להמרת שורות JSONL למילונים"""
        records = []
        for line in self.jsonl_data.strip().split('\n'):
            if line:
                records.append(json.loads(line))
        return records
