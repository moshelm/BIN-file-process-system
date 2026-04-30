import logging 
import flet as ft
from components.file_picker import PickerUploadFiles
from components.map import MapTableView
from components.table import TableService
from typing import Callable
from shared.schemas import GPSMessages

class DashboardView:
    def __init__(self, page: ft.Page):
        self.logger : logging.Logger = logging.getLogger(__name__)
        self.page : ft.Page = page
        self.layout: None = None

        self.picker_files_area : None  = None 
        self.result_display : ft.Text = ft.Text()
        self.map_container : ft.Container = ft.Container(height=400)
        self.table_container : ft.Container = ft.Container(height=300)

        self.page.title = "GPS Telemetry Dashboard"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.scroll = "auto"

    def build(self):
        self.layout = ft.Column([
            self.picker_files_area,
            self.result_display,
            ft.Divider(),
            self.map_container,
            ft.Divider(),
            self.table_container
        ])

    def show_error(self, msg: str):
        try:
            self.result_display.value = msg
            self.result_display.color = "red"
            self.page.update()
        except Exception:
            self.logger.error('show_error failed')

    def show_success(self):
        try:
            self.result_display.value = "Loaded successfully"
            self.result_display.color = "green"
            self.page.update()
        except Exception:
            self.logger.error('show_success failed')


    def update_map(self, data: GPSMessages, tile_url:str):
        try:
            self.map_container.content = MapTableView(data, tile_url)
        except Exception:
            self.logger.error('failed create table')
            raise
    def update_table(self, data: GPSMessages):
        try:
            table = TableService()
            self.table_container.content = table.build(data)
        except Exception:
            self.logger.error('failed create table')
            raise
    def create_picker_files(self,callback: Callable):
        try: 
            self.picker_files_area: ft.SafeArea = ft.SafeArea(content=PickerUploadFiles(self.page, callback).build())
        except Exception:
            self.logger.error('failed create picker file')
            raise
