import json

import flet as ft

from shared.logger_config import get_logger
from shared.schemas import GPSMessageResult, GPSMessages
from ui.src.services.api_client import ApiClient
from ui.src.utils.config import ConfigJsonFile
from ui.src.views.dashboard_view import DashboardView

logger = get_logger(__name__)

MAX_POINTS = 1000


class DashboardController:
    def __init__(self, view: DashboardView, config: ConfigJsonFile) -> None:
        self.view: DashboardView = view
        self.config: ConfigJsonFile = config
        self.api: ApiClient = ApiClient(config.bin_parser_gps)

    def create_picker(self) -> None:
        self.view.create_picker_files(self.handle_file_upload)

    async def handle_file_upload(self, local_file_path: str) -> None:
        try:
            gps_messages: GPSMessages | None = await self.api.upload_file_from_api(local_file_path)

            if not gps_messages:
                self.view.show_error("No data found")
                return

            gps_messages_normalize: list[GPSMessageResult] = normalize_messages(gps_messages)
            self.view.show_success()

            try:
                self.view.update_map(gps_messages_normalize, self.config.map_tile_url)

            except Exception as e:
                logger.error(e)
                self.view.show_error("Something went wrong with map")

            try:
                self.view.create_table_view(gps_messages_normalize)

            except Exception as e:
                logger.error(e)
                self.view.show_error("Something went wrong with table")

            stream_info_texts: list = []
            async for parse_result in self.api.get_information_about_parsers(
                self.config.bin_parsers_review, local_file_path
            ):
                parser_card = create_parser_result_card(parse_result)
                stream_info_texts.append(parser_card)
                self.view.update_sidebar(stream_info_texts)

        except Exception as e:
            logger.error(e)
            self.view.show_error("Something went wrong")


def normalize_messages(data: GPSMessages) -> list[GPSMessageResult]:
    try:
        step = max(1, len(data.messages) // MAX_POINTS)
        return data.messages[::step]
    except Exception:
        logger.error("Failed normalize messages")
        raise


def create_parser_result_card(json_string: str) -> ft.Card:
    try:
        data: dict = json.loads(json_string)

        parser_name = data.get("parser_name", "Unknown Parser")
        duration = data.get("duration", 0.0)
        count = data.get("count", 0)
        status = data.get("status", "PENDING")

        status_color = (
            ft.Colors.GREEN if status == "success" else ft.Colors.RED if status == "failed" else ft.Colors.AMBER
        )

        return ft.Card(
            elevation=5,  # יוצר הצללה יפה לכרטיסייה
            content=ft.Container(
                padding=15,
                bgcolor=ft.Colors.SURFACE_BRIGHT,
                border_radius=8,
                content=ft.Column(
                    spacing=5,
                    controls=[
                        ft.Text(
                            value=f"🛠️ {parser_name}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400
                        ),
                        ft.Divider(height=1, color=ft.Colors.OUTLINE),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.TIMER, size=16, color=ft.Colors.WHITE70),
                                ft.Text("Duration: ", weight=ft.FontWeight.W_500),
                                ft.Text(
                                    f"{duration:.2f} sec", weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_ACCENT
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.DATA_OBJECT, size=16, color=ft.Colors.WHITE70),
                                ft.Text(f"Messages: {count:,}"),  # פסיקים במספרים גדולים (למשל 7,500,000)
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=ft.Colors.WHITE70),
                                ft.Text("Status: "),
                                ft.Text(f"{status.upper()}", weight=ft.FontWeight.BOLD, color=status_color),
                            ]
                        ),
                    ],
                ),
            ),
        )
    except Exception as e:
        logger.error(f"error {str(e)}")
        return ft.Card(content=ft.Container(padding=10, content=ft.Text(f"Error reading result: {json_string}")))
