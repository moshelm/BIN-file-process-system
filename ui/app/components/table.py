import flet as ft
from shared.schemas import GPSMessageResult, GPSMessages


class TableService:
    @staticmethod
    def build(data :GPSMessages ):
        columns = [
            ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD))
            for col in GPSMessageResult.model_fields.keys()
        ]

        rows = []
        records = data.messages
        display_data : list[GPSMessageResult]= records[:1000] if len(records) > 1000 else records

        for row in display_data:
            obj_row = row.model_dump()
            cells = [
                ft.DataCell(ft.Text(str(obj_row.get(col, "")))) for col in GPSMessageResult.model_fields.keys()
            ]
            rows.append(ft.DataRow(cells=cells))

        data_table = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.Border.all(1, "white54"),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, "white24"),
            horizontal_lines=ft.border.BorderSide(1, "white24"),
            expand=True,
        )
        return ft.Column(
            controls=[data_table],
            scroll=ft.ScrollMode.ALWAYS,
            height=300,
            expand=True,
            width=800,
        )