import flet as ft
from ui.app.components.map import MapService, MapTableView
from ui.app.components.table import TableService
from ui.app.components.file_picker import PickerUploadFiles
import logging 
from config import Configuration


def  setup_logging():
    logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

def main(page: ft.Page):
    setup_logging()
    config = Configuration()
    
    page.title = "GPS Telemetry Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "auto"

    result_display = ft.Text()

    map_container = ft.Container(expand=True, height=400)
    table_container = ft.Container()
    
    def update_ui_with_data(raw_data):
        if not raw_data:
            result_display.value = "No data found"
            result_display.color = "red"
            page.update()
            return

        result_display.value = "Loaded successfully"
        result_display.color = "green"

        # map_table_view = MapTableView(raw_data)
        # page.add(map_table_view)
        # map_container.content =MapService().build(raw_data)
        map_container.content = MapTableView(raw_data, config.map_tile_url)
        table_container.content = TableService().build(raw_data)

        page.update()
    process_upload_file = PickerUploadFiles(page, config.bin_parser_uri)
    process_upload_file.process_picker_and_upload_files(update_ui_with_data)
    
    page.add(
        ft.Column([
            ft.Divider(),
            map_container,
            ft.Divider(),
            table_container
        ])
    )

ft.run(main)