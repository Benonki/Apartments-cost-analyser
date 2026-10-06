import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox


DB_FILE = Path(__file__).resolve().parent.parent / "apartments.db"
TABLE_NAME = "apartments"
ROWS_PER_PAGE = 250


class ApartmentsApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Analiza cen mieszkań w Polsce")
        self.geometry("1200x650")
        self.minsize(900, 500)

        self.current_page = 0
        self.total_rows = 0
        self.connection = None

        self.create_widgets()
        self.open_database()
        self.load_page()

    def create_widgets(self):
        title = ttk.Label(
            self,
            text="Dane mieszkań",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(15, 8))

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=15, pady=5)

        columns = (
            "id",
            "city",
            "area_m2",
            "rooms",
            "build_year",
            "centre_distance_km",
            "price_pln",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "city": "Miasto",
            "area_m2": "Powierzchnia [m²]",
            "rooms": "Liczba pokoi",
            "build_year": "Rok budowy",
            "centre_distance_km": "Odległość od centrum [km]",
            "price_pln": "Cena [zł]",
        }

        widths = {
            "id": 70,
            "city": 150,
            "area_m2": 150,
            "rooms": 120,
            "build_year": 120,
            "centre_distance_km": 210,
            "price_pln": 150,
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center")

        vertical_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        horizontal_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=15, pady=(5, 15))

        self.prev_button = ttk.Button(
            bottom_frame,
            text="← Poprzednia",
            command=self.previous_page
        )
        self.prev_button.pack(side="left")

        self.page_label = ttk.Label(bottom_frame, text="")
        self.page_label.pack(side="left", padx=15)

        self.next_button = ttk.Button(
            bottom_frame,
            text="Następna →",
            command=self.next_page
        )
        self.next_button.pack(side="left")

        self.count_label = ttk.Label(bottom_frame, text="")
        self.count_label.pack(side="right")

    def open_database(self):
        if not DB_FILE.exists():
            messagebox.showerror(
                "Brak bazy danych",
                f"Nie znaleziono pliku:\n{DB_FILE}\n\n"
                "Najpierw uruchom skrypt csv_to_db.py, aby utworzyć apartments.db."
            )
            self.destroy()
            return

        try:
            self.connection = sqlite3.connect(DB_FILE)
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            self.total_rows = cursor.fetchone()[0]
        except sqlite3.Error as error:
            messagebox.showerror("Błąd bazy danych", str(error))
            self.destroy()

    def load_page(self):
        if self.connection is None:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        offset = self.current_page * ROWS_PER_PAGE

        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            SELECT
                id,
                city,
                area_m2,
                rooms,
                build_year,
                centre_distance_km,
                price_pln
            FROM {TABLE_NAME}
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            (ROWS_PER_PAGE, offset),
        )

        for row in cursor.fetchall():
            display_row = list(row)

            if display_row[4] is None:
                display_row[4] = "brak danych"

            display_row[6] = f"{display_row[6]:,}".replace(",", " ")

            self.tree.insert("", "end", values=display_row)

        total_pages = max(1, (self.total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
        self.page_label.config(
            text=f"Strona {self.current_page + 1} z {total_pages}"
        )
        self.count_label.config(
            text=f"Liczba mieszkań w bazie: {self.total_rows}"
        )

        self.prev_button.config(
            state="normal" if self.current_page > 0 else "disabled"
        )
        self.next_button.config(
            state="normal"
            if self.current_page < total_pages - 1
            else "disabled"
        )

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

    def next_page(self):
        total_pages = max(1, (self.total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_page()

    def destroy(self):
        if self.connection is not None:
            self.connection.close()
        super().destroy()

