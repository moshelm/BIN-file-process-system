import flet as ft
from ui.src.components.file_picker import PickerUploadFiles
from ui.src.components.map import MapTableViewBuilder
from ui.src.components.table import create_table

from typing import Callable
from shared.schemas import GPSMessages
from shared.logger_config import get_logger

logger = get_logger(__name__)

class DashboardView:
    def __init__(self, page: ft.Page):
        self.page : ft.Page = page
        self.layout: None = None
        self.sidebar_column: ft.Column = ft.Column(spacing=10)
        self.result_display : ft.Text = ft.Text()
        self.picker_files_container : ft.Container  = ft.Container(height=100,width=800) 
        self.map_container : ft.Container = ft.Container(height=400,width=800)
        self.table_container : ft.Container = ft.Container(height=300,width=800)
        
        self._initialize_page()

        self.picker_file = PickerUploadFiles(self.page)

    def _initialize_page(self):
        self.page.title = "GPS Telemetry Dashboard"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.scroll = "auto"

    def build(self):
        # 1. התוכן הראשי (בלי שום expand!)
        main_content = ft.Column([
            self.picker_files_container,
            self.result_display,
            ft.Divider(),
            self.map_container,
            ft.Divider(),
            self.table_container
        ])

        # 2. עמודת הסיידבר (מוכנה לקבל את הטקסטים שלך)
        sidebar_content = ft.Container(
            content=self.sidebar_column, 
            padding=10,
            border=ft.Border(left=ft.BorderSide(1, ft.Colors.OUTLINE))
        )

        # 3. הפריסה הראשית בעזרת ResponsiveRow - הכי יציב שיש
        self.layout = ft.ResponsiveRow(
            controls=[
                # צד שמאל: תופס 9 מתוך 12 חלקים במסכים בינוניים/גדולים (ו-12 במסכים קטנים)
                ft.Column(
                    col={"sm": 12, "md": 9}, 
                    controls=[main_content]
                ),
                # צד ימין: תופס 3 מתוך 12 חלקים
                ft.Column(
                    col={"sm": 12, "md": 3},
                    controls=[sidebar_content]
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.START
        )

    def update_sidebar(self, cards_items: list[ft.Card]):
        try:
            self.sidebar_column.controls.clear()
            
            for card in cards_items:
                if card: 
                    self.sidebar_column.controls.append(card)
            
            self.page.update()
        except Exception as e:
            logger.error(f'failed update sidebar: {e}')

    def show_error(self, msg: str):
        try:
            self.result_display.value = msg
            self.result_display.color = "red"
            self.page.update()
        except Exception:
            logger.error('show_error failed')

    def show_success(self):
        try:
            self.result_display.value = "Loaded successfully"
            self.result_display.color = "green"
            self.page.update()
        except Exception:
            logger.error('show_success failed')


    def update_map(self, data: GPSMessages, tile_url:str):
        try:
            map_component = MapTableViewBuilder(data, tile_url)
           
            self.map_container.content = map_component.build()
        except Exception:
            logger.error('failed create map')
            raise

    def create_table_view(self, data: GPSMessages):
        try:
            self.table_container.content = create_table(data)
        except Exception:
            logger.error('failed create table')
            raise

    def create_picker_files(self,callback: Callable):
        try: 
            self.picker_file.get_callback_function(callback)

            self.picker_files_container.content = self.picker_file.create_picker_file_view()
        except Exception:
            logger.error('failed create picker file')
            raise
