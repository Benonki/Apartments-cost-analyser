import math
import sqlite3
from collections import Counter
from statistics import mean, median
from tkinter import ttk, messagebox

from headerTooltip import TreeviewHeaderTooltip


class StatisticsTab(ttk.Frame):
    VARIABLES = {
        "area_m2": "Powierzchnia [m²]",
        "rooms": "Liczba pokoi",
        "build_year": "Rok budowy",
        "centre_distance_km": "Odległość od centrum [km]",
        "price_pln": "Cena [zł]",
    }

    def __init__(self, parent, connection, table_name):
        super().__init__(parent)

        self.connection = connection
        self.table_name = table_name

        self.create_widgets()
        self.load_distribution_measures()

    def create_widgets(self):
        statistics_frame = ttk.Frame(self)
        statistics_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = (
            "variable",
            "n",
            "mean",
            "median",
            "mode",
            "min",
            "max",
            "range",
            "variance",
            "stddev",
            "cv",
            "skewness",
            "kurtosis",
        )

        self.statistics_tree = ttk.Treeview(
            statistics_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "variable": "Wielkość",
            "n": "N",
            "mean": "Średnia",
            "median": "Mediana",
            "mode": "Dominanta",
            "min": "Minimum",
            "max": "Maksimum",
            "range": "Rozstęp",
            "variance": "Wariancja",
            "stddev": "Odch. standardowe",
            "cv": "Wsp. zmienności [%]",
            "skewness": "Skośność",
            "kurtosis": "Kurtoza nadmiarowa",
        }

        widths = {
            "variable": 190,
            "n": 80,
            "mean": 120,
            "median": 120,
            "mode": 140,
            "min": 120,
            "max": 120,
            "range": 120,
            "variance": 130,
            "stddev": 140,
            "cv": 155,
            "skewness": 110,
            "kurtosis": 145,
        }

        for column in columns:
            self.statistics_tree.heading(column, text=headings[column])
            self.statistics_tree.column(
                column,
                width=widths[column],
                minwidth=80,
                anchor="center"
            )

        header_descriptions = {
            "variable": "Analizowana wielkość z bazy danych.",
            "n": "Liczba obserwacji wykorzystanych do obliczeń.",
            "mean": "Średnia arytmetyczna wszystkich wartości.",
            "median": "Wartość środkowa po uporządkowaniu danych.",
            "mode": "Najczęściej występująca wartość w zbiorze.",
            "min": "Najmniejsza zaobserwowana wartość.",
            "max": "Największa zaobserwowana wartość.",
            "range": "Różnica między maksimum a minimum.",
            "variance": (
                "Miara rozproszenia danych wokół średniej. "
                "Tutaj liczona jako wariancja z próby (n−1)."
            ),
            "stddev": (
                "Pierwiastek z wariancji; pokazuje typową skalę "
                "odchylenia od średniej."
            ),
            "cv": (
                "Odchylenie standardowe względem średniej, wyrażone w %. "
            ),
            "skewness": (
                "Określa asymetrię rozkładu: dodatnia oznacza dłuższy "
                "ogon po prawej, ujemna po lewej."
            ),
            "kurtosis": (
                "Opisuje koncentrację i ciężkość ogonów rozkładu. "
                "Dla rozkładu normalnego kurtoza nadmiarowa wynosi 0."
            ),
        }

        self.header_tooltip = TreeviewHeaderTooltip(
            self.statistics_tree,
            columns,
            header_descriptions,
        )

        vertical_scrollbar = ttk.Scrollbar(
            statistics_frame,
            orient="vertical",
            command=self.statistics_tree.yview
        )
        horizontal_scrollbar = ttk.Scrollbar(
            statistics_frame,
            orient="horizontal",
            command=self.statistics_tree.xview
        )

        self.statistics_tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set
        )

        self.statistics_tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        statistics_frame.rowconfigure(0, weight=1)
        statistics_frame.columnconfigure(0, weight=1)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        ttk.Button(
            bottom_frame,
            text="Przelicz miary",
            command=self.load_distribution_measures
        ).pack(side="left")

        ttk.Label(
            bottom_frame,
            text=(
                "Wariancja i odchylenie standardowe: próbkowe (n−1). "
                "Skośność: skorygowany współczynnik Fishera-Pearsona. "
                "Kurtoza: nadmiarowa (0 dla rozkładu normalnego)."
            )
        ).pack(side="left", padx=15)

    def load_distribution_measures(self):
        for item in self.statistics_tree.get_children():
            self.statistics_tree.delete(item)

        cursor = self.connection.cursor()

        try:
            for column_name, display_name in self.VARIABLES.items():
                cursor.execute(
                    f"SELECT {column_name} FROM {self.table_name} "
                    f"WHERE {column_name} IS NOT NULL"
                )
                values = [float(row[0]) for row in cursor.fetchall()]

                measures = self.calculate_measures(values)

                self.statistics_tree.insert(
                    "",
                    "end",
                    values=(
                        display_name,
                        measures["n"],
                        self.format_number(measures["mean"]),
                        self.format_number(measures["median"]),
                        self.format_mode(measures["mode"]),
                        self.format_number(measures["min"]),
                        self.format_number(measures["max"]),
                        self.format_number(measures["range"]),
                        self.format_number(measures["variance"]),
                        self.format_number(measures["stddev"]),
                        self.format_number(measures["cv"]),
                        self.format_number(measures["skewness"]),
                        self.format_number(measures["kurtosis"]),
                    )
                )
        except (sqlite3.Error, TypeError, ValueError) as error:
            messagebox.showerror(
                "Błąd obliczeń",
                f"Nie udało się wyznaczyć miar rozkładu:\n{error}"
            )

    @staticmethod
    def calculate_measures(values):
        n = len(values)

        if n == 0:
            return {
                "n": 0,
                "mean": None,
                "median": None,
                "mode": None,
                "min": None,
                "max": None,
                "range": None,
                "variance": None,
                "stddev": None,
                "cv": None,
                "skewness": None,
                "kurtosis": None,
            }

        avg = mean(values)
        med = median(values)
        minimum = min(values)
        maximum = max(values)
        data_range = maximum - minimum

        counts = Counter(values)
        max_count = max(counts.values())
        modes = sorted(value for value, count in counts.items() if count == max_count)
        mode_value = None if max_count == 1 else modes

        if n >= 2:
            sum_squared_deviations = sum((x - avg) ** 2 for x in values)
            variance = sum_squared_deviations / (n - 1)
            stddev = math.sqrt(variance)
        else:
            variance = None
            stddev = None

        if stddev is not None and avg != 0:
            cv = (stddev / abs(avg)) * 100
        else:
            cv = None

        if n >= 3 and stddev not in (None, 0):
            skewness = (
                n / ((n - 1) * (n - 2))
            ) * sum(((x - avg) / stddev) ** 3 for x in values)
        else:
            skewness = None

        if n >= 4 and stddev not in (None, 0):
            standardized_fourth_sum = sum(
                ((x - avg) / stddev) ** 4 for x in values
            )
            kurtosis = (
                (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3)))
                * standardized_fourth_sum
                - (3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
            )
        else:
            kurtosis = None

        return {
            "n": n,
            "mean": avg,
            "median": med,
            "mode": mode_value,
            "min": minimum,
            "max": maximum,
            "range": data_range,
            "variance": variance,
            "stddev": stddev,
            "cv": cv,
            "skewness": skewness,
            "kurtosis": kurtosis,
        }

    @staticmethod
    def format_number(value):
        if value is None:
            return "—"

        if math.isclose(value, round(value), abs_tol=1e-10):
            return f"{int(round(value)):,}".replace(",", " ")

        formatted = f"{value:,.4f}"
        formatted = formatted.rstrip("0").rstrip(".")
        return formatted.replace(",", " ")

    @staticmethod
    def format_mode(mode_values):
        if mode_values is None:
            return "brak"

        if not mode_values:
            return "—"

        visible_modes = mode_values[:3]
        text = ", ".join(
            StatisticsTab.format_number(value)
            for value in visible_modes
        )

        if len(mode_values) > 3:
            text += ", ..."

        return text
