import logging
import uvicorn
import flet as ft
from components.file_picker import PickerUploadFiles
from components.map import MapTableView
from components.table import TableService
from config import Configuration
from flet_web.fastapi import app as flet_fastapi_app


def setup_logging():
    logging.basicConfig(
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )


def main(page: ft.Page):
    try:
        setup_logging()
        logger = logging.getLogger(__name__)

        config = Configuration()

        page.title = "GPS Telemetry Dashboard"
        page.theme_mode = ft.ThemeMode.DARK
        page.scroll = "auto"

        result_display = ft.Text()

        map_container = ft.Container(height=400, width=800)
        table_container = ft.Container(height=300)

        def update_ui_with_data(raw_data):
            try:
                if not raw_data:
                    result_display.value = "No data found"
                    result_display.color = "red"
                    page.update()
                    return

                result_display.value = "Loaded successfully"
                result_display.color = "green"

                map_container.content = MapTableView(raw_data, config.map_tile_url)
                table_container.content = TableService().build(raw_data)

                page.update()
                
            except Exception:
                logger.error()

        process_upload_file = PickerUploadFiles(page, config.bin_parser_uri)
        process_upload_file.process_picker_and_upload_files(update_ui_with_data)

        page.add(
            result_display,
            ft.Column([ft.Divider(), map_container, ft.Divider(), table_container], expand=True),
        )
    except Exception:
        logger.error()



app = flet_fastapi_app(main, secret_key="dsfagw32", upload_dir="/tmp/uploads")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
