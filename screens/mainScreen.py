import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

from statisticsTab import StatisticsTab
from tableTab import TableTab
from correlationTab import CorrelationTab
from chartsTab import ChartsTab


DB_FILE = Path(__file__).resolve().parent.parent / "apartments.db"
TABLE_NAME = "apartments"


class ApartmentsApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Analiza cen mieszkań w Polsce")
        self.geometry("1450x720")
        self.minsize(1000, 550)

        self.connection = None

        self.open_database()
        if self.connection is not None:
            self.create_widgets()

    def create_widgets(self):
        title = ttk.Label(
            self,
            text="Analiza danych mieszkań",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(15, 8))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.table_tab = TableTab(
            notebook,
            connection=self.connection,
            table_name=TABLE_NAME
        )
        self.statistics_tab = StatisticsTab(
            notebook,
            connection=self.connection,
            table_name=TABLE_NAME
        )
        self.correlation_tab = CorrelationTab(
            notebook,
            connection=self.connection,
            table_name=TABLE_NAME
        )
        self.charts_tab = ChartsTab(
            notebook,
            connection=self.connection,
            table_name=TABLE_NAME
        )

        notebook.add(self.table_tab, text="Tabela")
        notebook.add(self.statistics_tab, text="Miary rozkładu")
        notebook.add(self.correlation_tab, text="Korelacje")
        notebook.add(self.charts_tab, text="Wykresy")

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
        except sqlite3.Error as error:
            messagebox.showerror("Błąd bazy danych", str(error))
            self.destroy()

    def destroy(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        super().destroy()
