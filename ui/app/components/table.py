import flet as ft

FIELDS = ['TimeUS', 'Status', 'Lat','Lng','Alt','Spd']

class TableService():
    @staticmethod
    def build(raw_data:list[dict], required_columns :list = FIELDS):
        columns = [ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD)) for col in required_columns]

        rows = []
        
        display_data = raw_data[:1000] if len(raw_data) > 1000 else raw_data

        for row in display_data:
            cells = [ft.DataCell(ft.Text(str(row.get(col, "")))) for col in required_columns]
            rows.append(ft.DataRow(cells=cells))

        data_table = ft.DataTable(
            columns=columns, 
            rows=rows,
            border=ft.Border.all(1, "white54"),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, "white24"),
            horizontal_lines=ft.border.BorderSide(1, "white24")
        )
        return ft.Column(
            controls=[data_table],
            scroll=ft.ScrollMode.ALWAYS,
            height=300 # אפשר לשנות את הגובה לפי הצורך
        )
# ft.Column([self._build_table()], expand=1, scroll=ft.ScrollMode.AUTO),

# def _build_table(self):
#         """יצירת טבלת הנתונים"""
#         return ft.DataTable(
#             columns=[
#                 ft.DataColumn(ft.Text("Latitude")),
#                 ft.DataColumn(ft.Text("Longitude")),
#             ],
#             rows=[
#                 ft.DataRow(
#                     cells=[
#                         ft.DataCell(ft.Text(str(r["Lat"]))),
#                         ft.DataCell(ft.Text(str(r["Lng"]))),
#                     ]
#                 ) for r in self.records
#             ]
#         )
