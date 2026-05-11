import os

import flet as ft
import uvicorn
from flet_web.fastapi import app as flet_fastapi_app

from shared.logger_config import get_logger
from ui.src.controllers.dashboard_controller import DashboardController
from ui.src.utils.config import config_data
from ui.src.views.dashboard_view import DashboardView

logger = get_logger(__name__)


def main(page: ft.Page):
    try:
        view: DashboardView = DashboardView(page)

        controller: DashboardController = DashboardController(view, config_data)

        controller.create_picker()

        view.build()

        page.add(view.layout)

    except Exception:
        logger.error("failed running", exc_info=True)


if __name__ == "__main__":
    PORT = int(os.getenv("PROCESS_SERVICE_PORT", "8000"))
    HOST = os.getenv("PROCESS_SERVICE_HOST", "0.0.0.0")
    SECRET_KEY = os.getenv("SECRET_KEY_FLET_UI", "dsfagw32")

    app = flet_fastapi_app(main, secret_key=SECRET_KEY, upload_dir="/tmp/uploads")

    uvicorn.run(app, host=HOST, port=PORT)
