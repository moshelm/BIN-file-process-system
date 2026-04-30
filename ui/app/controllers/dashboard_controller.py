import logging 
from config import Configuration
from views.dashboard_view import DashboardView
from services.api_client import ApiClient
from shared.schemas import GPSMessages

class DashboardController:
    def __init__(self, view: DashboardView, config: Configuration):
        self.view : DashboardView = view
        self.config : Configuration = config
        self.api = ApiClient(config.bin_parser_uri)
        
        self.logger : logging.Logger = logging.getLogger(__name__)
    
    def create_picker(self):
        self.view.create_picker_files(self.handle_file_upload)

    async def handle_file_upload(self, local_file_path: str):
        try:
            gps_messages : GPSMessages | None = await self.api.upload_file(local_file_path)
            
            if not gps_messages:
                self.view.show_error("No data found")
                return

            self.view.show_success()

            try:
                self.view.update_map(gps_messages, self.config.map_tile_url)
            
            except Exception as e:
                self.logger.error(e)
                self.view.show_error("Something went wrong with map")
            
            try:
                self.view.update_table(gps_messages)
            
            except Exception as e:
                self.logger.error(e)
                self.view.show_error("Something went wrong with table")

        except Exception as e:
            self.logger.error(e)
            self.view.show_error("Something went wrong")