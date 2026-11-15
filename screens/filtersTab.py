import math
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox


class ApartmentFilters:
    def __init__(self):
        self.year_from = None
        self.year_to = None
        self.price_from = None
        self.price_to = None

    def set_ranges(self, year_from=None, year_to=None, price_from=None, price_to=None):
        self.year_from = year_from
        self.year_to = year_to
        self.price_from = price_from
        self.price_to = price_to

    def as_sql(self):
        conditions = []
        params = []
        for column, operator, value in (
            ("build_year", ">=", self.year_from),
            ("build_year", "<=", self.year_to),
            ("price_pln", ">=", self.price_from),
            ("price_pln", "<=", self.price_to),
        ):
            if value is not None:
                conditions.append(f"{column} {operator} ?")
                params.append(value)
        sql = "" if not conditions else " AND " + " AND ".join(conditions)
        return sql, tuple(params)


class FiltersTab(ttk.Frame):
    def __init__(self, parent, connection, table_name, filters, on_apply):
        super().__init__(parent)
        self.connection = connection
        self.table_name = table_name
        self.filters = filters
        self.on_apply = on_apply

        self.year_from_var = tk.StringVar()
        self.year_to_var = tk.StringVar()
        self.price_from_var = tk.StringVar()
        self.price_to_var = tk.StringVar()
        self.summary_var = tk.StringVar()
        self.year_hint_var = tk.StringVar()
        self.price_hint_var = tk.StringVar()

        self.create_widgets()
        self.load_database_ranges()
        self.update_summary()

    def create_widgets(self):
        content = ttk.Frame(self, padding=22)
        content.pack(anchor="nw", fill="x")
        content.columnconfigure(0, weight=1)

        ttk.Label(
            content,
            text="Ustal zakresy i kliknij Zastosuj filtry. Puste pole oznacza brak ograniczenia.",
            wraplength=850,
        ).grid(row=1, column=0, sticky="w", pady=(0, 20))

        years = ttk.LabelFrame(content, text="Rok budowy", padding=15)
        years.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self.add_range_inputs(years, self.year_from_var, self.year_to_var)
        ttk.Label(years, textvariable=self.year_hint_var).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(10, 0)
        )

        prices = ttk.LabelFrame(content, text="Cena mieszkania [zł]", padding=15)
        prices.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        self.add_range_inputs(prices, self.price_from_var, self.price_to_var)
        ttk.Label(prices, textvariable=self.price_hint_var).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(10, 0)
        )

        actions = ttk.Frame(content)
        actions.grid(row=4, column=0, sticky="w", pady=(6, 15))
        ttk.Button(
            actions, text="Zastosuj filtry", command=self.apply_filters
        ).pack(side="left")
        ttk.Button(
            actions, text="Wyczyść filtry", command=self.clear_filters
        ).pack(side="left", padx=12)

        ttk.Label(
            content, textvariable=self.summary_var, font=("Segoe UI", 11, "bold")
        ).grid(row=5, column=0, sticky="w")

    def add_range_inputs(self, frame, lower_var, upper_var):
        ttk.Label(frame, text="Od:").grid(row=0, column=0, sticky="w")
        lower_entry = ttk.Entry(frame, textvariable=lower_var, width=19)
        lower_entry.grid(row=0, column=1, sticky="w", padx=(8, 30))
        ttk.Label(frame, text="Do:").grid(row=0, column=2, sticky="w")
        upper_entry = ttk.Entry(frame, textvariable=upper_var, width=19)
        upper_entry.grid(row=0, column=3, sticky="w", padx=(8, 0))
        for entry in (lower_entry, upper_entry):
            entry.bind("<Return>", lambda _event: self.apply_filters())

    @staticmethod
    def format_number(value):
        if value is None:
            return "brak danych"
        return f"{value:,.0f}".replace(",", " ")

    def load_database_ranges(self):
        try:
            cursor = self.connection.execute(
                f"SELECT MIN(build_year), MAX(build_year), "
                f"MIN(price_pln), MAX(price_pln) FROM {self.table_name}"
            )
            year_min, year_max, price_min, price_max = cursor.fetchone()
            self.year_hint_var.set(
                f"Dostępne lata: {self.format_number(year_min)} – {self.format_number(year_max)}"
            )
            self.price_hint_var.set(
                f"Dostępne ceny: {self.format_number(price_min)} – "
                f"{self.format_number(price_max)} zł"
            )
        except sqlite3.Error as error:
            messagebox.showerror("Błąd bazy danych", str(error))

    @staticmethod
    def parse_year(value):
        text = value.strip()
        if not text:
            return None
        if not text.isdecimal() or int(text) < 1:
            raise ValueError("Rok budowy musi być dodatnią liczbą całkowitą.")
        return int(text)

    @staticmethod
    def parse_price(value):
        text = value.strip().replace(" ", "").replace("\u00a0", "").replace(",", ".")
        if not text:
            return None
        try:
            number = float(text)
        except ValueError as error:
            raise ValueError("Cena musi być liczbą (np. 500000 lub 500 000,50).") from error
        if not math.isfinite(number) or number < 0:
            raise ValueError("Cena musi być liczbą nieujemną.")
        return number

    def apply_filters(self):
        try:
            year_from = self.parse_year(self.year_from_var.get())
            year_to = self.parse_year(self.year_to_var.get())
            price_from = self.parse_price(self.price_from_var.get())
            price_to = self.parse_price(self.price_to_var.get())
            if year_from is not None and year_to is not None and year_from > year_to:
                raise ValueError("Rok 'Od' nie może być późniejszy niż rok 'Do'.")
            if price_from is not None and price_to is not None and price_from > price_to:
                raise ValueError("Cena 'Od' nie może być większa od ceny 'Do'.")
        except ValueError as error:
            messagebox.showwarning("Nieprawidłowy filtr", str(error), parent=self)
            return

        self.filters.set_ranges(year_from, year_to, price_from, price_to)
        self.on_apply()
        self.update_summary()

    def clear_filters(self):
        for value in (
            self.year_from_var, self.year_to_var,
            self.price_from_var, self.price_to_var,
        ):
            value.set("")
        self.apply_filters()

    def update_summary(self):
        try:
            sql_filter, params = self.filters.as_sql()
            matched = self.connection.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE 1=1{sql_filter}",
                params,
            ).fetchone()[0]
            total = self.connection.execute(
                f"SELECT COUNT(*) FROM {self.table_name}"
            ).fetchone()[0]
            self.summary_var.set(
                f"Wybrane mieszkania: {matched:,} z {total:,}".replace(",", " ")
            )
        except sqlite3.Error as error:
            messagebox.showerror("Błąd bazy danych", str(error))
