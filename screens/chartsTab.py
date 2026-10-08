import math
import tkinter as tk
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
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.scroll_area = tk.Canvas(self, highlightthickness=0)
        self.scroll_area.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))

        vertical_scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.scroll_area.yview
        )
        vertical_scrollbar.grid(row=0, column=1, sticky="ns", pady=(10, 0))
        horizontal_scrollbar = ttk.Scrollbar(
            self, orient="horizontal", command=self.scroll_area.xview
        )
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew", padx=(10, 0))
        self.scroll_area.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        self.figure = Figure(figsize=(13.5, 12), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.scroll_area)
        self.plot_widget = self.canvas.get_tk_widget()
        self.scroll_area.create_window((0, 0), window=self.plot_widget, anchor="nw")
        self.plot_widget.bind("<Configure>", self._update_scroll_region)
        self.scroll_area.bind("<Configure>", self._update_scroll_region)

        for target in (self.scroll_area, self.plot_widget):
            target.bind("<MouseWheel>", self._on_mousewheel)
            target.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
            target.bind("<Button-4>", lambda event: self.scroll_area.yview_scroll(-1, "units"))
            target.bind("<Button-5>", lambda event: self.scroll_area.yview_scroll(1, "units"))

        self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 10))
        self.toolbar.set_message = lambda message: None

    def _update_scroll_region(self, _event=None):
        self.scroll_area.configure(scrollregion=self.scroll_area.bbox("all"))

    def _on_mousewheel(self, event):
        if event.delta:
            steps = -1 if event.delta > 0 else 1
            self.scroll_area.yview_scroll(steps * max(1, abs(event.delta) // 120), "units")
            return "break"

    def _on_shift_mousewheel(self, event):
        if event.delta:
            steps = -1 if event.delta > 0 else 1
            self.scroll_area.xview_scroll(steps * max(1, abs(event.delta) // 120), "units")
            return "break"

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

        axes = self.figure.subplots(3, 2)

        self.draw_price_histogram(axes[0, 0], data)
        self.draw_area_price_scatter(axes[0, 1], data)

        self.draw_city_prices(axes[1, 0], data)
        self.draw_price_per_square_meter(axes[1, 1], data)

        self.draw_rooms_pictogram(axes[2, 0], data)
        self.draw_rooms_pie(axes[2, 1], data)

        self.figure.tight_layout(pad=3, h_pad=4, w_pad=3)
        self.canvas.draw()
        self._update_scroll_region()

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
    @staticmethod
    def draw_rooms_pie(axis, data):
        rooms = pd.to_numeric(data["rooms"], errors="coerce").dropna()
        rooms = rooms[(rooms > 0) & (rooms % 1 == 0)]
        counts = rooms.astype(int).value_counts().sort_index()

        axis.set_title("Podział mieszkań według liczby pokoi")
        if counts.empty:
            axis.text(0.5, 0.5, "Brak danych", ha="center", va="center", transform=axis.transAxes)
            return

        total = counts.sum()
        labels = [
            f"{int(rooms)} pok. — {count:,}".replace(",", " ")
            + f" mieszkań ({count / total * 100:.1f}%)"
            for rooms, count in counts.items()
        ]
        axis.pie(
            counts.values,
            labels=None,
            autopct=lambda percent: f"{percent:.1f}%" if percent >= 3 else "",
            startangle=90,
            pctdistance=0.73,
            wedgeprops={"edgecolor": "white", "linewidth": 1},
        )
        axis.legend(labels, loc="center left", bbox_to_anchor=(0.98, 0.5), fontsize=8)
        axis.set_aspect("equal")

    @staticmethod
    def draw_price_per_square_meter(axis, data):
        values = data[["city", "area_m2", "price_pln"]].dropna().copy()
        values["city"] = values["city"].astype(str).str.strip()
        values = values[
            (values["city"] != "") &
            (values["area_m2"] > 0) &
            (values["price_pln"] > 0)
        ]
        values["price_m2"] = values["price_pln"] / values["area_m2"]
        mean_prices = values.groupby("city")["price_m2"].mean()
        city_order = (
            data.dropna(subset=["city", "price_pln"])
            .groupby("city")["price_pln"]
            .mean()
            .sort_values()
            .index
        )
        mean_prices = mean_prices.reindex(city_order).dropna()

        axis.set_title("Średnia cena za m² według miasta")
        axis.set_xlabel("Średnia cena [zł/m²]")
        if mean_prices.empty:
            axis.text(0.5, 0.5, "Brak danych", ha="center", va="center", transform=axis.transAxes)
            return

        axis.barh(mean_prices.index.str.title(), mean_prices.values, color="#76B7B2")
        axis.grid(axis="x", alpha=0.25)
        axis.set_axisbelow(True)
