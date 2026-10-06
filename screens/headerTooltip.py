import tkinter as tk


class TreeviewHeaderTooltip:
    def __init__(self, treeview, columns, descriptions, delay_ms=350):
        self.treeview = treeview
        self.columns = list(columns)
        self.descriptions = descriptions
        self.delay_ms = delay_ms

        self.tooltip_window = None
        self.after_id = None
        self.active_column = None
        self.mouse_x_root = 0
        self.mouse_y_root = 0

        self.treeview.bind("<Motion>", self._on_motion, add="+")
        self.treeview.bind("<Leave>", self._on_leave, add="+")
        self.treeview.bind("<ButtonPress>", self._hide, add="+")

    def _on_motion(self, event):
        self.mouse_x_root = event.x_root
        self.mouse_y_root = event.y_root

        if self.treeview.identify_region(event.x, event.y) != "heading":
            self._cancel_pending()
            self._hide()
            self.active_column = None
            return

        column_token = self.treeview.identify_column(event.x)
        try:
            column_index = int(column_token[1:]) - 1
            column_name = self.columns[column_index]
        except (ValueError, IndexError):
            self._cancel_pending()
            self._hide()
            self.active_column = None
            return

        if column_name == self.active_column:
            if self.tooltip_window is not None:
                self._move_tooltip()
            return

        self._cancel_pending()
        self._hide()
        self.active_column = column_name

        if column_name in self.descriptions:
            self.after_id = self.treeview.after(
                self.delay_ms,
                lambda: self._show(column_name)
            )

    def _on_leave(self, _event):
        self._cancel_pending()
        self._hide()
        self.active_column = None

    def _show(self, column_name):
        self.after_id = None
        description = self.descriptions.get(column_name)
        if not description or column_name != self.active_column:
            return

        self.tooltip_window = tk.Toplevel(self.treeview)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.attributes("-topmost", True)

        label = tk.Label(
            self.tooltip_window,
            text=description,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padx=7,
            pady=5,
            font=("Segoe UI", 9),
            wraplength=320,
        )
        label.pack()
        self._move_tooltip()

    def _move_tooltip(self):
        if self.tooltip_window is None:
            return

        x = self.mouse_x_root + 14
        y = self.mouse_y_root + 18
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

    def _cancel_pending(self):
        if self.after_id is not None:
            self.treeview.after_cancel(self.after_id)
            self.after_id = None

    def _hide(self, _event=None):
        if self.tooltip_window is not None:
            self.tooltip_window.destroy()
            self.tooltip_window = None
