import plotly.graph_objects as go
import plotly.io as pio
import os
import webbrowser
import flet as ft
import flet_map as fmap
import os

FIELDS = {'TimeUS', 'Status', 'Lat','Lng','Alt','Spd'}

class MapService():
    
    @staticmethod
    def build(raw_data: list[dict[str,int]], fields: set = FIELDS):
        
        extracted_data, hover_texts = process_telemetry_data(raw_data, fields)

        fig = go.Figure(go.Scattermapbox(
            lat=extracted_data['Lat'],
            lon=extracted_data['Lng'],
            mode='markers',
            marker=dict(size=8, color=extracted_data['Status'], colorscale='Viridis'),
            text=hover_texts,
            hoverinfo='text'
        ))

        fig.update_layout(
            mapbox_style="open-street-map",
            margin=dict(l=0, r=0, t=0, b=0)
        )

        html =  pio.to_html(fig, include_plotlyjs="cdn")
        
        file_path = os.path.abspath("map.html")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        webbrowser.open(f"file:///{file_path}")

        return ft.Markdown(html)

class MapTableView(ft.Row):
    def __init__(self, data: list[dict], map_tile_url: str):
        super().__init__()
        self.expand = True # הרכיב יתפרס על כל המקום הפנוי
        self.data = data[:1000]
        self.map_tile_url = map_tile_url

        # אתחול ועיבוד נתונים
        self.records = self.data
        self.center_lat, self.center_lon = self._calculate_center()
        
        self.controls = [
            ft.Container(self._build_map(), expand=2, border=ft.Border.all(1, ft.Colors.OUTLINE), border_radius=10)
        ]

    
    def _calculate_center(self):
        """פונקציה פנימית לחישוב מרכז אזור ה-GPS"""
        if not self.records:
            return 0, 0
        lat = sum(r["Lat"] for r in self.records) / len(self.records)
        lon = sum(r["Lng"] for r in self.records) / len(self.records)
        return lat, lon

    # def _build_table(self):
    #     """יצירת טבלת הנתונים"""
    #     return ft.DataTable(
    #         columns=[
    #             ft.DataColumn(ft.Text("Latitude")),
    #             ft.DataColumn(ft.Text("Longitude")),
    #         ],
    #         rows=[
    #             ft.DataRow(
    #                 cells=[
    #                     ft.DataCell(ft.Text(str(r["Lat"]))),
    #                     ft.DataCell(ft.Text(str(r["Lng"]))),
    #                 ]
    #             ) for r in self.records
    #         ]
    #     )

    def _build_map(self):
        map_widget = fmap.Map(
            expand=True,
            initial_center=fmap.MapLatitudeLongitude(self.center_lat, self.center_lon),
            initial_zoom=8,
            layers=[
                fmap.TileLayer(url_template=self.map_tile_url),
                fmap.MarkerLayer(
                    markers=[
                        fmap.Marker(
                            content=ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED),
                            coordinates=fmap.MapLatitudeLongitude(r["Lat"], r["Lng"]),
                        )
                        for r in self.records
                        if r["Lat"] and r["Lng"]
                    ]
                )
            ]
        )
        
        # ✅ ADD THIS PART (THIS IS THE FIX)
        return ft.Stack([
            map_widget,
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
            )
        ])
    

def process_telemetry_data(raw_data:list[dict], fields:set[str]):  
    extracted_data = {field: [] for field in fields}
    hover_texts = []

    for row in raw_data:
        for field in fields:
            extracted_data[field].append(row.get(field, 0))
    
        details = [f"<b>{f}</b>: {row.get(f, 'N/A')}" for f in fields]
        hover_texts.append("<br>".join(details))

    return extracted_data, hover_texts
