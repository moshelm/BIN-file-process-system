import flet as ft
import plotly.graph_objects as go
import plotly.io as pio
from logic import fetch_bin_data


def main(page: ft.Page):
    page.title = "GPS Telemetry Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "auto"

    # UI elements
    user_input = ft.TextField(label="Insert file name", width=300)
    result_display = ft.Text()

    map_container = ft.Container(expand=True)
    table_container = ft.Container()

    # 🔥 MAIN BUTTON LOGIC
    def on_click(e):
        file_name = user_input.value

        raw_data = fetch_bin_data(file_name)

        if not raw_data:
            result_display.value = "No data found"
            result_display.color = "red"
            page.update()
            return

        result_display.value = "Loaded successfully"
        result_display.color = "green"

        # ---- MAP ----
        
        lats = [row.get('Lat', 0) for row in raw_data]
        lngs = [row.get('Lng', 0) for row in raw_data]
        times = [row.get('TimeUS', 0) for row in raw_data]

        hover_texts = [
            f"Spd: {row.get('Spd', 0)} | Alt: {row.get('Alt', 0)}"
            for row in raw_data
        ]

        fig = go.Figure(go.Scattermapbox(
            lat=lats,
            lon=lngs,
            mode='markers',
            marker=dict(size=8, color=times, colorscale='Viridis'),
            text=hover_texts,
            hoverinfo='text'
        ))

        fig.update_layout(
            mapbox_style="open-street-map",
            margin=dict(l=0, r=0, t=0, b=0)
        )

        html = pio.to_html(fig, include_plotlyjs="cdn")

        map_container.content = ft.Markdown(html)
        import os
        import webbrowser

        file_path = os.path.abspath("map.html")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        webbrowser.open(f"file:///{file_path}")

        # ---- TABLE ----
        required_columns = ['TimeUS', 'Lat', 'Lng', 'Alt', 'Spd']

     
        columns = [ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD)) for col in required_columns]

        rows = []
        
        display_data = raw_data[:1000] if len(raw_data) > 1000 else raw_data

        for row in display_data:
            cells = [ft.DataCell(ft.Text(str(row.get(col, "")))) for col in required_columns]
            rows.append(ft.DataRow(cells=cells))

        data_table = ft.DataTable(
            columns=columns, 
            rows=rows,
            border=ft.border.all(1, "white54"),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, "white24"),
            horizontal_lines=ft.border.BorderSide(1, "white24")
        )

        table_container.content = ft.Column(
            controls=[data_table],
            scroll=ft.ScrollMode.ALWAYS,
            height=300 # אפשר לשנות את הגובה לפי הצורך
        )

        page.update()

    # Button
    button = ft.ElevatedButton("Run", on_click=on_click)

    # Layout
    page.add(
        ft.Column([
            user_input,
            button,
            result_display,
            ft.Divider(),
            map_container,
            ft.Divider(),
            table_container
        ])
    )


ft.app(target=main)