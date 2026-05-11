import flet as ft
import flet_map as fmap

from shared.logger_config import get_logger
from shared.schemas import GPSMessageResult

logger = get_logger(__name__)


class MapTableViewBuilder:
    def __init__(self, data: list[GPSMessageResult], map_tile_url: str):

        self.records = data
        self.map_tile_url = map_tile_url
        self.center_lat, self.center_lon = self._calculate_center()

        self.info_text = ft.Text(
            color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD, value="Hover over a point to see details..."
        )

    def _calculate_center(self):
        if not self.records:
            return 0, 0
        center_lat = sum(record.Lat for record in self.records) / len(self.records)
        center_lon = sum(record.Lng for record in self.records) / len(self.records)
        return center_lat, center_lon

    def handle_point_hover(self, e: ft.Event[ft.Button]):
        if e.data == "true":
            point_data: GPSMessageResult = e.control.data
            if point_data:
                self.info_text.value = f"Lat: {point_data.Lat:.2f} | Lng: {point_data.Lng:.2f}"
                self.info_text.update()
        else:
            self.info_text.value = "Hover over a point to see details..."
            self.info_text.update()

    def _create_marker(
        self,
        record: GPSMessageResult,
        *,
        width: int,
        height: int,
        tooltip: str,
        inner_content: ft.Control,
        bgcolor: str | None = None,
        border_radius: int = 100,
    ) -> fmap.Marker:

        return fmap.Marker(
            coordinates=fmap.MapLatitudeLongitude(
                record.Lat,
                record.Lng,
            ),
            content=ft.Container(
                width=width,
                height=height,
                alignment=ft.Alignment.CENTER,
                bgcolor=bgcolor,
                border_radius=border_radius,
                data=record,
                on_hover=self.handle_point_hover,
                tooltip=tooltip,
                content=inner_content,
            ),
        )

    def create_end_point(self, record: GPSMessageResult):
        return self._create_marker(
            record=record,
            width=28,
            height=28,
            bgcolor=ft.Colors.RED,
            border_radius=14,
            tooltip=f"END | Speed: {record.Spd} | Alt: {record.Alt}",
            inner_content=ft.Icon(
                ft.Icons.FLAG,
                color=ft.Colors.WHITE,
                size=16,
            ),
        )

    def create_start_point(self, record: GPSMessageResult):
        return self._create_marker(
            record=record,
            width=28,
            height=28,
            bgcolor=ft.Colors.GREEN,
            border_radius=14,
            tooltip=f"START | Speed: {record.Spd} | Alt: {record.Alt}",
            inner_content=ft.Icon(
                ft.Icons.PLAY_ARROW,
                color=ft.Colors.WHITE,
                size=16,
            ),
        )

    def create_point(self, record: GPSMessageResult):
        return self._create_marker(
            record=record,
            width=16,
            height=16,
            tooltip=f"Speed: {record.Spd} | Alt: {record.Alt}",
            inner_content=ft.Container(
                width=6,
                height=6,
                bgcolor=ft.Colors.BLUE,
                border_radius=16,
            ),
        )

    def build(self) -> ft.Column:
        path_coordinates: list[fmap.MapLatitudeLongitude] = []
        markers: list[fmap.Marker] = []

        for index, record in enumerate(self.records):

            if not (record.Lat and record.Lng):
                continue

            coordinates = fmap.MapLatitudeLongitude(
                record.Lat,
                record.Lng,
            )

            path_coordinates.append(coordinates)

            is_start = index == 0
            is_end = index == len(self.records) - 1

            if is_start:
                markers.append(self.create_start_point(record))

            elif is_end:
                markers.append(self.create_end_point(record))
            else:
                markers.append(self.create_point(record))

        map_widget = fmap.Map(
            expand=True,
            initial_center=fmap.MapLatitudeLongitude(
                self.center_lat,
                self.center_lon,
            ),
            initial_zoom=8,
            layers=[
                fmap.TileLayer(
                    url_template=self.map_tile_url,
                    expand=True,
                ),
                fmap.PolylineLayer(
                    polylines=[
                        fmap.PolylineMarker(
                            coordinates=path_coordinates,
                            stroke_width=3,
                            color=ft.Colors.RED_ACCENT,
                        )
                    ]
                ),
                fmap.MarkerLayer(markers=markers),
            ],
        )

        return ft.Column(
            controls=[
                self.info_text,
                map_widget,
                ft.Container(
                    content=ft.Text(
                        "© OpenStreetMap contributors",
                        size=12,
                        color=ft.Colors.WHITE,
                    ),
                    bgcolor=ft.Colors.BLACK,
                    padding=5,
                    border_radius=5,
                    alignment=ft.Alignment.CENTER_RIGHT,
                ),
            ],
            expand=True,
            width=800,
            height=300,
        )
