import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

from statisticsTab import StatisticsTab
from tableTab import TableTab
from correlationTab import CorrelationTab
from chartsTab import ChartsTab
from filtersTab import ApartmentFilters, FiltersTab


DB_FILE = Path(__file__).resolve().parent.parent / "apartments.db"
TABLE_NAME = "apartments"


class ApartmentsApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Analiza cen mieszkań w Polsce")
        self.geometry("1450x720")
        self.minsize(1000, 550)

        self.connection = None
        self.filters = ApartmentFilters()

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

        tabs_container = ttk.Frame(self)
        tabs_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        tabs_container.columnconfigure(0, weight=1)
        tabs_container.rowconfigure(1, weight=1)

        tab_bar = ttk.Frame(tabs_container)
        tab_bar.grid(row=0, column=0, sticky="ew")
        tab_bar.columnconfigure(1, weight=1)

        left_tabs = ttk.Frame(tab_bar)
        left_tabs.grid(row=0, column=0, sticky="w")

        style = ttk.Style(self)
        style.configure("ApartmentTab.Toolbutton", padding=(16, 8))
        self.selected_tab = tk.StringVar(value="table")

        for key, label in (
            ("table", "Tabela"),
            ("statistics", "Miary rozkładu"),
            ("correlation", "Korelacje"),
            ("charts", "Wykresy"),
        ):
            ttk.Radiobutton(
                left_tabs,
                text=label,
                variable=self.selected_tab,
                value=key,
                style="ApartmentTab.Toolbutton",
                command=self.show_selected_tab,
            ).pack(side="left", padx=(0, 3))

        self.filters_tab_button = ttk.Radiobutton(
            tab_bar,
            text="Filtry",
            variable=self.selected_tab,
            value="filters",
            style="ApartmentTab.Toolbutton",
            command=self.show_selected_tab,
        )
        self.filters_tab_button.grid(row=0, column=2, sticky="e")
        self.pages_frame = ttk.Frame(tabs_container, borderwidth=1, relief="solid")
        self.pages_frame.grid(row=1, column=0, sticky="nsew")

        self.table_tab = TableTab(
            self.pages_frame,
            connection=self.connection,
            table_name=TABLE_NAME,
            filters=self.filters
        )
        self.statistics_tab = StatisticsTab(
            self.pages_frame,
            connection=self.connection,
            table_name=TABLE_NAME,
            filters=self.filters
        )
        self.correlation_tab = CorrelationTab(
            self.pages_frame,
            connection=self.connection,
            table_name=TABLE_NAME,
            filters=self.filters
        )
        self.charts_tab = ChartsTab(
            self.pages_frame,
            connection=self.connection,
            table_name=TABLE_NAME,
            filters=self.filters
        )
        self.filters_tab = FiltersTab(
            self.pages_frame,
            connection=self.connection,
            table_name=TABLE_NAME,
            filters=self.filters,
            on_apply=self.reload_all_tabs,
        )

        self.tab_pages = {
            "table": self.table_tab,
            "statistics": self.statistics_tab,
            "correlation": self.correlation_tab,
            "charts": self.charts_tab,
            "filters": self.filters_tab,
        }
        for page in self.tab_pages.values():
            page.place(x=0, y=0, relwidth=1, relheight=1)
        self.show_selected_tab()

    def show_selected_tab(self):
        self.tab_pages[self.selected_tab.get()].tkraise()

    def reload_all_tabs(self):
        self.table_tab.current_page = 0
        self.table_tab.refresh_count()
        self.table_tab.load_page()
        self.statistics_tab.load_distribution_measures()
        self.correlation_tab.load_correlations()
        self.charts_tab.load_charts()

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
