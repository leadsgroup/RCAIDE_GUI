# RCAIDE_GUI/tabs/geometry/widgets/powertrain/distributors/base_distributor_widget.py

# Created: Jun 2026, M. Clarke

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox

from tabs.geometry.widgets import GeometryDataWidget


class BaseDistributorWidget(GeometryDataWidget):
    """Base class for all powertrain distributor widgets.

    Provides the inline connectivity UI — a row of checkboxes for propulsors and
    a row of checkboxes for sources.  Subclasses set ``distributor_type`` and call
    ``_build_connectivity_rows()`` to insert the checkbox rows into their layout.

    Connectivity data is populated lazily: names loaded from a saved file go into
    ``_pending_propulsors`` / ``_pending_sources`` and are applied the next time
    ``set_propulsors()`` / ``set_sources()`` is called (i.e. when the user clicks
    "Refresh Connections" or when a file loads the powertrain widget).
    """

    distributor_type = ""

    def __init__(self, index, on_delete):
        super().__init__()
        self.index = index
        self.on_delete = on_delete
        self._propulsor_checkboxes: dict[str, QCheckBox] = {}
        self._source_checkboxes: dict[str, QCheckBox] = {}
        self._pending_propulsors: list[str] = []
        self._pending_sources: list[str] = []

    # ── Checkbox helpers ────────────────────────────────────────────────────

    def _rebuild_checkbox_row(self, row_layout, checkboxes, names, pending):
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
        self._rebuild_checkbox_row(
            self._propulsor_row, self._propulsor_checkboxes, names, self._pending_propulsors,
        )
        self._pending_propulsors = []

    def set_sources(self, names: list[str]):
        self._rebuild_checkbox_row(
            self._source_row, self._source_checkboxes, names, self._pending_sources,
        )
        self._pending_sources = []

    def delete_button_pressed(self):
        if self.on_delete:
            self.on_delete(self.index)

    def _build_connectivity_rows(self, layout):
        """Append propulsor and source inline checkbox rows to a layout."""
        layout.addWidget(QLabel("<i>Connected Propulsors:</i>"))
        self._propulsor_container = QWidget()
        self._propulsor_row = QHBoxLayout(self._propulsor_container)
        self._propulsor_row.setContentsMargins(0, 0, 0, 0)
        self._propulsor_row.addWidget(QLabel("(click Refresh Connections to load)"))
        layout.addWidget(self._propulsor_container)

        layout.addWidget(QLabel("<i>Connected Sources:</i>"))
        self._source_container = QWidget()
        self._source_row = QHBoxLayout(self._source_container)
        self._source_row.setContentsMargins(0, 0, 0, 0)
        self._source_row.addWidget(QLabel("(click Refresh Connections to load)"))
        layout.addWidget(self._source_container)

    def _connectivity_data(self) -> dict:
        return {
            "assigned_propulsors": [n for n, cb in self._propulsor_checkboxes.items() if cb.isChecked()],
            "assigned_sources":    [n for n, cb in self._source_checkboxes.items() if cb.isChecked()],
        }

    def _load_connectivity(self, data: dict):
        self._pending_propulsors = list(data.get("assigned_propulsors", []))
        self._pending_sources    = list(data.get("assigned_sources", []))
