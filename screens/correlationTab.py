from tkinter import ttk, messagebox

import pandas as pd


class CorrelationTab(ttk.Frame):
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
        self.load_correlations()

    def create_widgets(self):
        table_frame = ttk.Frame(self)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(10, 5)
        )

        columns = (
            "first_variable",
            "second_variable",
            "observations",
            "coefficient",
            "interpretation",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        self.tree.heading("first_variable", text="Pierwsza wielkość")
        self.tree.heading("second_variable", text="Druga wielkość")
        self.tree.heading("observations", text="N")
        self.tree.heading("coefficient", text="Korelacja Pearsona")
        self.tree.heading("interpretation", text="Interpretacja")

        self.tree.column("first_variable", width=230, anchor="center")
        self.tree.column("second_variable", width=230, anchor="center")
        self.tree.column("observations", width=80, anchor="center")
        self.tree.column("coefficient", width=160, anchor="center")
        self.tree.column("interpretation", width=250, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        ttk.Button(
            bottom_frame,
            text="Przelicz korelacje",
            command=self.load_correlations
        ).pack(side="left")

        ttk.Label(
            bottom_frame,
            text=(
                "Współczynnik Pearsona przyjmuje wartości od -1 do 1. "
                "Korelacja nie oznacza związku przyczynowego."
            )
        ).pack(side="left", padx=15)

    def load_correlations(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        column_names = list(self.VARIABLES)

        query = (
            f"SELECT {', '.join(column_names)} "
            f"FROM {self.table_name}"
        )

        try:
            data = pd.read_sql_query(query, self.connection)

            for column_name in column_names:
                data[column_name] = pd.to_numeric(
                    data[column_name],
                    errors="coerce"
                )

            correlation_matrix = data.corr(
                method="pearson",
                min_periods=2
            )

            for first_index, first_column in enumerate(column_names):
                for second_column in column_names[first_index + 1:]:
                    coefficient = correlation_matrix.loc[
                        first_column,
                        second_column
                    ]

                    observations = (
                        data[[first_column, second_column]]
                        .dropna()
                        .shape[0]
                    )

                    if pd.isna(coefficient):
                        coefficient_text = "brak danych"
                        interpretation = "nie można obliczyć"
                    else:
                        coefficient_text = f"{coefficient:.4f}"
                        interpretation = self.interpret_correlation(
                            coefficient
                        )

                    self.tree.insert(
                        "",
                        "end",
                        values=(
                            self.VARIABLES[first_column],
                            self.VARIABLES[second_column],
                            observations,
                            coefficient_text,
                            interpretation,
                        )
                    )

        except Exception as error:
            messagebox.showerror(
                "Błąd korelacji",
                f"Nie udało się obliczyć korelacji:\n{error}"
            )

    @staticmethod
    def interpret_correlation(value):
        absolute_value = abs(value)

        if absolute_value < 0.2:
            strength = "bardzo słaba"
        elif absolute_value < 0.4:
            strength = "słaba"
        elif absolute_value < 0.6:
            strength = "umiarkowana"
        elif absolute_value < 0.8:
            strength = "silna"
        else:
            strength = "bardzo silna"

        if value > 0:
            direction = "dodatnia"
        elif value < 0:
            direction = "ujemna"
        else:
            direction = "brak kierunku"

        return f"{strength}, {direction}"