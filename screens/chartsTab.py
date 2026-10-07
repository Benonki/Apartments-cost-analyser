import math
from tkinter import ttk, messagebox

import pandas as pd
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from matplotlib.figure import Figure
from matplotlib.path import Path


class ChartsTab(ttk.Frame):
    APARTMENTS_PER_ICON = 500

    def __init__(self, parent, connection, table_name):
        super().__init__(parent)

        self.connection = connection
        self.table_name = table_name

        self.create_widgets()
        self.load_charts()

    def create_widgets(self):
        self.figure = Figure(figsize=(12, 6), dpi=100)

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=self
        )
        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(10, 0)
        )

        toolbar = NavigationToolbar2Tk(
            self.canvas,
            self,
            pack_toolbar=False
        )
        toolbar.update()
        toolbar.pack(fill="x", padx=10, pady=(0, 10))

    def load_charts(self):
        query = f"""
            SELECT
                city,
                area_m2,
                rooms,
                centre_distance_km,
                price_pln
            FROM {self.table_name}
        """

        try:
            data = pd.read_sql_query(query, self.connection)

            numeric_columns = [
                "area_m2",
                "rooms",
                "centre_distance_km",
                "price_pln",
            ]

            for column in numeric_columns:
                data[column] = pd.to_numeric(
                    data[column],
                    errors="coerce"
                )

            self.draw_charts(data)

        except Exception as error:
            messagebox.showerror(
                "Błąd wykresów",
                f"Nie udało się utworzyć wykresów:\n{error}"
            )

    def draw_charts(self, data):
        self.figure.clear()

        axes = self.figure.subplots(2, 2)

        self.draw_price_histogram(axes[0, 0], data)
        self.draw_city_prices(axes[0, 1], data)
        self.draw_area_price_scatter(axes[1, 0], data)
        self.draw_rooms_pictogram(axes[1, 1], data)

        self.figure.tight_layout(pad=2)
        self.canvas.draw()

    @staticmethod
    def draw_price_histogram(axis, data):
        prices = data["price_pln"].dropna() / 1_000_000

        axis.hist(
            prices,
            bins=30,
            color="#4C78A8",
            edgecolor="white"
        )

        axis.set_title("Rozkład cen mieszkań")
        axis.set_xlabel("Cena [mln zł]")
        axis.set_ylabel("Liczba mieszkań")
        axis.grid(axis="y", alpha=0.25)

    @staticmethod
    def draw_city_prices(axis, data):
        city_prices = (
            data.dropna(subset=["city", "price_pln"])
            .groupby("city")["price_pln"]
            .mean()
            .sort_values()
            / 1_000_000
        )

        axis.barh(
            city_prices.index.str.title(),
            city_prices.values,
            color="#59A14F"
        )

        axis.set_title("Średnia cena według miasta")
        axis.set_xlabel("Średnia cena [mln zł]")
        axis.grid(axis="x", alpha=0.25)

    @staticmethod
    def draw_area_price_scatter(axis, data):
        plot_data = data[
            ["area_m2", "price_pln"]
        ].dropna()

        axis.scatter(
            plot_data["area_m2"],
            plot_data["price_pln"] / 1_000_000,
            s=10,
            alpha=0.25,
            color="#E15759"
        )

        axis.set_title("Powierzchnia a cena")
        axis.set_xlabel("Powierzchnia [m²]")
        axis.set_ylabel("Cena [mln zł]")
        axis.grid(alpha=0.25)

    def draw_rooms_pictogram(self, axis, data):
        room_counts = (
            data["rooms"]
            .dropna()
            .astype(int)
            .value_counts()
            .sort_index()
        )

        vertices = [
            (-1.0, -1.0),
            (1.0, -1.0),
            (1.0, 0.1),
            (0.0, 1.0),
            (-1.0, 0.1),
            (-1.0, -1.0),
        ]

        codes = [
            Path.MOVETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.CLOSEPOLY,
        ]

        house_marker = Path(vertices, codes)

        labels = []
        maximum_icons = 0

        for row_number, (rooms, count) in enumerate(
            room_counts.items()
        ):
            icon_count = math.ceil(
                count / self.APARTMENTS_PER_ICON
            )
            maximum_icons = max(maximum_icons, icon_count)

            axis.scatter(
                range(icon_count),
                [row_number] * icon_count,
                marker=house_marker,
                s=180,
                color="#F28E2B"
            )

            labels.append(
                f"{rooms} pok. ({count} mieszkań)"
            )

        axis.set_yticks(range(len(labels)))
        axis.set_yticklabels(labels)
        axis.set_xticks([])
        axis.set_xlim(-1, maximum_icons)
        axis.invert_yaxis()

        axis.set_title(
            "Liczba mieszkań według liczby pokoi\n"
            f"1 domek ≈ {self.APARTMENTS_PER_ICON} mieszkań"
        )

        for border in axis.spines.values():
            border.set_visible(False)