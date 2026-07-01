# RCAIDE_GUI/tabs/geometry/widgets/powertrain/distributors/fuel_line_widget.py

# Created: Dec 2025, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QCheckBox)

from tabs.geometry.widgets import GeometryDataWidget


class FuelLineWidget(GeometryDataWidget):
    def __init__(self, index, on_delete, data_values=None):
        super(FuelLineWidget, self).__init__()

        self.index = index
        self.on_delete = on_delete
        self._propulsor_checkboxes: dict[str, QCheckBox] = {}
        self._source_checkboxes: dict[str, QCheckBox] = {}
        # Checked names loaded from saved data — applied on the next refresh.
        self._pending_propulsors: list[str] = []
        self._pending_sources: list[str] = []

        layout = self.create_scroll_layout()

        # ── Name + delete row ──────────────────────────────────────────────
        row = QHBoxLayout()
        row.addWidget(QLabel("Fuel Line Name:"))
        self.section_name_edit = QLineEdit(self)
        row.addWidget(self.section_name_edit)
        del_btn = QPushButton("Delete", self)
        del_btn.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        del_btn.setMaximumWidth(80)
        del_btn.clicked.connect(self.delete_button_pressed)
        row.addWidget(del_btn)
        layout.addLayout(row)

        # ── Propulsor checkboxes ───────────────────────────────────────────
        layout.addWidget(QLabel("<i>Connected Propulsors:</i>"))
        self._propulsor_container = QWidget()
        self._propulsor_row = QHBoxLayout(self._propulsor_container)
        self._propulsor_row.setContentsMargins(0, 0, 0, 0)
        self._propulsor_row.addWidget(QLabel("(click Refresh Connections to load)"))
        layout.addWidget(self._propulsor_container)

        # ── Source checkboxes ──────────────────────────────────────────────
        layout.addWidget(QLabel("<i>Connected Sources:</i>"))
        self._source_container = QWidget()
        self._source_row = QHBoxLayout(self._source_container)
        self._source_row.setContentsMargins(0, 0, 0, 0)
        self._source_row.addWidget(QLabel("(click Refresh Connections to load)"))
        layout.addWidget(self._source_container)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        if data_values:
            self.load_data_values(data_values)

    # ── Checkbox helpers ───────────────────────────────────────────────────

    def _rebuild_checkbox_row(self, row_layout, checkboxes, names, pending):
        """Rebuild a checkbox row, preserving checked state and applying pending names."""
        wanted = {n for n, cb in checkboxes.items() if cb.isChecked()} | set(pending)
        while row_layout.count():
            item = row_layout.takeAt(0)
            w = item.widget() if item else None
            if w:
                w.deleteLater()
        checkboxes.clear()
        if not names:
            row_layout.addWidget(QLabel("(none defined)"))
            return
        for name in names:
            cb = QCheckBox(name)
            cb.setChecked(name in wanted)
            checkboxes[name] = cb
            row_layout.addWidget(cb)
        row_layout.addStretch()

    def set_propulsors(self, names: list[str]):
        """Refresh propulsor checkboxes from the current propulsor list."""
        self._rebuild_checkbox_row(
            self._propulsor_row, self._propulsor_checkboxes,
            names, self._pending_propulsors,
        )
        self._pending_propulsors = []

    def set_sources(self, names: list[str]):
        """Refresh source checkboxes from the current source list."""
        self._rebuild_checkbox_row(
            self._source_row, self._source_checkboxes,
            names, self._pending_sources,
        )
        self._pending_sources = []

    # ── Data API ───────────────────────────────────────────────────────────

    def get_data_values(self):
        data = {
            "distributor name":    self.section_name_edit.text(),
            "assigned_propulsors": [n for n, cb in self._propulsor_checkboxes.items() if cb.isChecked()],
            "assigned_sources":    [n for n, cb in self._source_checkboxes.items() if cb.isChecked()],
        }
        return data, self.create_rcaide_structure(data)

    def load_data_values(self, data):
        if "distributor name" in data:
            self.section_name_edit.setText(data["distributor name"])
        # Pending names are applied on the next set_propulsors / set_sources call.
        self._pending_propulsors = list(data.get("assigned_propulsors", []))
        self._pending_sources    = list(data.get("assigned_sources",    []))

    def create_rcaide_structure(self, data):
        line = RCAIDE.Library.Components.Powertrain.Distributors.Fuel_Line()
        line.tag = data["distributor name"]
        return line

    def delete_button_pressed(self):
        if self.on_delete is None:
            return
        self.on_delete(self.index)

    def create_scroll_layout(self):
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        self.setLayout(layout)
        return layout
