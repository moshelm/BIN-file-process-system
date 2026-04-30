import flet as ft
import flet_map as fmap
from shared.schemas import GPSMessages, GPSMessageResult


class MapTableView(ft.Row):
    def __init__(self, data: GPSMessages, map_tile_url: str):
        super().__init__()
        self.expand = True
        MAX_POINTS = 1000

        # נחשב קפיצה (step) כדי לפרוס את הדגימות על פני כל המערך
        step = max(1, len(data.messages) // MAX_POINTS)

        # ניקח נתונים בדילוגים שווים (slicing עם step)
        self.records = data.messages[::step]

        self.map_tile_url = map_tile_url

        self.center_lat, self.center_lon = self._calculate_center()

        self.controls = [
            ft.Container(
                self._build_map(),
                expand=2,
                border=ft.Border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
            )
        ]

    def _calculate_center(self):
        if not self.records:
            return 0, 0
        lat = sum(record.Lat for record in self.records) / len(self.records)
        lon = sum(record.Lng for record in self.records) / len(self.records)
        return lat, lon

    def on_point_click(self, info_text: ft.Text, point_data: GPSMessageResult):
        def handler(e):
            info_text.value = f"Speed: {point_data.Spd} | Alt: {point_data.Alt}"
            self.page.update()

        return handler

    def _build_map(self):
        info_text = ft.Text(
            color=ft.Colors.BLACK, top=10, left=10, weight=ft.FontWeight.BOLD
        )

        path_coordinates = [
            fmap.MapLatitudeLongitude(record.Lat, record.Lng)
            for record in self.records
            if record.Lat and record.Lng
        ]

        polyline_layer = fmap.PolylineLayer(
            polylines=[
                fmap.PolylineMarker(
                    coordinates=path_coordinates,
                    stroke_width=3,  # עובי הקו
                    color=ft.Colors.RED_ACCENT,  # צבע הקו
                )
            ]
        )

        # --- 2. יצירת הנקודות בנפרד (התחלה, אמצע, סוף) ---
        markers = []

        if self.records:
            # א. הוספת כל נקודות האמצע (חותכים את הראשונה והאחרונה בעזרת [1:-1])
            for record in self.records[1:-1]:
                if record.Lat and record.Lng:
                    markers.append(
                        fmap.Marker(
                            coordinates=fmap.MapLatitudeLongitude(
                                record.Lat, record.Lng
                            ),
                            content=ft.Container(
                                width=6,
                                height=6,
                                bgcolor=ft.Colors.BLUE,
                                border_radius=100,
                                on_hover=self.on_point_click(info_text, record),
                            ),
                        )
                    )

            # ב. הוספת סמן התחלה - נקודה גדולה וירוקה עם חץ (Play)
            start_record = self.records[0]
            markers.append(
                fmap.Marker(
                    coordinates=fmap.MapLatitudeLongitude(
                        start_record.Lat, start_record.Lng
                    ),
                    content=ft.Container(
                        content=ft.Icon(
                            ft.Icons.PLAY_ARROW, color=ft.Colors.WHITE, size=16
                        ),
                        width=28,
                        height=28,
                        bgcolor=ft.Colors.GREEN,
                        border_radius=14,
                        alignment=ft.Alignment.CENTER,
                        on_hover=self.on_point_click(info_text, start_record),
                    ),
                )
            )

            # ג. הוספת סמן סיום - נקודה גדולה ואדומה עם דגל סיום
            end_record = self.records[-1]
            markers.append(
                fmap.Marker(
                    coordinates=fmap.MapLatitudeLongitude(
                        end_record.Lat, end_record.Lng
                    ),
                    content=ft.Container(
                        content=ft.Icon(ft.Icons.FLAG, color=ft.Colors.WHITE, size=16),
                        width=28,
                        height=28,
                        bgcolor=ft.Colors.RED,
                        border_radius=14,
                        alignment=ft.Alignment.CENTER,
                        on_hover=self.on_point_click(info_text, end_record),
                    ),
                )
            )

        marker_layer = fmap.MarkerLayer(markers=markers)

        # הרכבת המפה
        map_widget = fmap.Map(
            expand=True,
            initial_center=fmap.MapLatitudeLongitude(self.center_lat, self.center_lon),
            initial_zoom=8,
            layers=[
                fmap.TileLayer(url_template=self.map_tile_url, expand=True),
                polyline_layer,  # ציור הקו הרציף
                marker_layer,  # ציור הנקודות והסמנים (מעל הקו)
            ],
        )

        return ft.Stack(
            [
                map_widget,
                info_text,
                ft.Container(
                    content=ft.Text(
                        "© OpenStreetMap contributors",
                        size=12,
                        color=ft.Colors.WHITE,
                    ),
                    bottom=5,
                    right=5,
                    bgcolor=ft.Colors.BLACK,
                    padding=5,
                    border_radius=5,
                ),
            ],
            expand=True,
        )


def process_telemetry_data(raw_data: list[dict], fields: set[str]):
    extracted_data: dict[str, list[dict]] = {field: [] for field in fields}
    hover_texts = []

    for row in raw_data:
        for field in fields:
            extracted_data[field].append(row.get(field, 0))

        details = [f"<b>{f}</b>: {row.get(f, 'N/A')}" for f in fields]
        hover_texts.append("<br>".join(details))

    return extracted_data, hover_texts
