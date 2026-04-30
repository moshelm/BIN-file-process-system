import logging

import flet as ft
import uvicorn
from config import Configuration
from flet_web.fastapi import app as flet_fastapi_app
from views.dashboard_view import DashboardView
from controllers.dashboard_controller import DashboardController


def setup_logging():
    logging.basicConfig(
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )


def main(page: ft.Page):
    try:
        setup_logging()
        logger : logging.Logger = logging.getLogger(__name__)

        config : Configuration = Configuration()
        
        view : DashboardView = DashboardView(page)

        controller : DashboardController = DashboardController(view, config)
        
        controller.create_picker()

        view.build()

        page.add(view.layout)
    except Exception:
        logger.error('failed running',exc_info=True)

app = flet_fastapi_app(main, secret_key="dsfagw32", upload_dir="/tmp/uploads")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
