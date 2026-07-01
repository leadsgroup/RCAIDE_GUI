# RCAIDE_GUI/tabs/geometry/frames/powertrain/connections/connection_matrix_frame.py
#
# Created: Jul 2026, M. Clarke

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QCheckBox, QScrollArea, QFrame, QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import Qt


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()
        child = item.layout()
        if child:
            _clear_layout(child)


class ConnectionMatrixFrame(QWidget):
    """Two-section connection matrix: Propulsors → Distributors and Sources → Distributors.

    Columns are distributors; rows are propulsors (top section) then energy sources
    (bottom section).  A ticked checkbox at [row, col] means that component is
    connected to that distributor.

    Call ``refresh()`` after component lists change to rebuild the grid while
    preserving existing checkbox states for components whose names haven't changed.
    Call ``get_connectivity()`` at save time to read the current matrix state.
    """

    def __init__(self):
        super().__init__()

        # {prop_name: {dist_name: QCheckBox}}
        self._propulsor_checks: dict[str, dict[str, QCheckBox]] = {}
        # {src_name:  {dist_name: QCheckBox}}
        self._source_checks: dict[str, dict[str, QCheckBox]] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)

        # Scroll area wraps the grid so it handles large networks
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(6)
        self._grid.setContentsMargins(4, 4, 4, 4)

        scroll = QScrollArea()
        scroll.setWidget(self._grid_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        self._empty_label = QLabel(
            "Add distributors, propulsors, and sources,\n"
            "then click  Refresh Connections  to populate the matrix."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: grey; font-style: italic;")
        outer.addWidget(self._empty_label)

    # ── Public API ─────────────────────────────────────────────────────────

    def refresh(
        self,
        propulsor_names: list[str],
        source_names: list[str],
        distributor_names: list[str],
        connectivity: dict[str, dict],
    ):
        """Rebuild the matrix.

        ``connectivity`` maps distributor name → dict with keys
        ``"assigned_propulsors"`` and ``"assigned_sources"`` (lists of names).
        Existing checkbox states are preserved for names that still exist.
        """
        # Snapshot current checked state before clearing
        old_prop = {
            p: {d: cb.isChecked() for d, cb in dmap.items()}
            for p, dmap in self._propulsor_checks.items()
        }
        old_src = {
            s: {d: cb.isChecked() for d, cb in dmap.items()}
            for s, dmap in self._source_checks.items()
        }

        _clear_layout(self._grid)
        self._propulsor_checks.clear()
        self._source_checks.clear()

        has_content = bool(distributor_names and (propulsor_names or source_names))
        self._empty_label.setVisible(not has_content)
        self._grid_widget.setVisible(has_content)

        if not has_content:
            return

        row = 0

        # ── Column headers (distributor names) ────────────────────────────
        self._grid.addWidget(QLabel(""), row, 0)  # top-left corner cell
        for col, dist_name in enumerate(distributor_names, start=1):
            lbl = QLabel(f"<b>{dist_name}</b>")
            lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            lbl.setWordWrap(True)
            lbl.setMaximumWidth(120)
            self._grid.addWidget(lbl, row, col)
        row += 1

        # ── Propulsors section ────────────────────────────────────────────
        if propulsor_names:
            row = self._add_section_header("Propulsors", len(distributor_names), row)
            for prop_name in propulsor_names:
                row = self._add_component_row(
                    prop_name, distributor_names, connectivity,
                    key="assigned_propulsors",
                    checks_dict=self._propulsor_checks,
                    old_state=old_prop,
                    grid_row=row,
                )

        # ── Sources section ───────────────────────────────────────────────
        if source_names:
            row = self._add_section_header("Energy Sources", len(distributor_names), row)
            for src_name in source_names:
                row = self._add_component_row(
                    src_name, distributor_names, connectivity,
                    key="assigned_sources",
                    checks_dict=self._source_checks,
                    old_state=old_src,
                    grid_row=row,
                )

        # Trailing stretch
        self._grid.setRowStretch(row, 1)
        self._grid_widget.adjustSize()

    def get_connectivity(self) -> dict[str, dict]:
        """Return ``{dist_name: {'assigned_propulsors': [...], 'assigned_sources': [...]}}``."""
        result: dict[str, dict] = {}

        for prop_name, dist_map in self._propulsor_checks.items():
            for dist_name, cb in dist_map.items():
                if cb.isChecked():
                    entry = result.setdefault(
                        dist_name, {"assigned_propulsors": [], "assigned_sources": []}
                    )
                    entry["assigned_propulsors"].append(prop_name)

        for src_name, dist_map in self._source_checks.items():
            for dist_name, cb in dist_map.items():
                if cb.isChecked():
                    entry = result.setdefault(
                        dist_name, {"assigned_propulsors": [], "assigned_sources": []}
                    )
                    entry["assigned_sources"].append(src_name)

        return result

    # ── Private helpers ────────────────────────────────────────────────────

    def _add_section_header(self, title: str, n_cols: int, row: int) -> int:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self._grid.addWidget(line, row, 0, 1, n_cols + 1)
        row += 1

        lbl = QLabel(f"<b>{title}</b>")
        lbl.setStyleSheet("padding: 2px 0px;")
        self._grid.addWidget(lbl, row, 0, 1, n_cols + 1)
        row += 1
        return row

    def _add_component_row(
        self,
        name: str,
        distributor_names: list[str],
        connectivity: dict[str, dict],
        key: str,
        checks_dict: dict,
        old_state: dict,
        grid_row: int,
    ) -> int:
        checks_dict[name] = {}

        lbl = QLabel(name)
        lbl.setMinimumWidth(140)
        self._grid.addWidget(lbl, grid_row, 0)

        for col, dist_name in enumerate(distributor_names, start=1):
            # Priority: previously checked state > loaded connectivity
            if name in old_state and dist_name in old_state[name]:
                checked = old_state[name][dist_name]
            else:
                checked = name in connectivity.get(dist_name, {}).get(key, [])

            cb = QCheckBox()
            cb.setChecked(checked)
            cb.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            checks_dict[name][dist_name] = cb
            self._grid.addWidget(cb, grid_row, col, alignment=Qt.AlignmentFlag.AlignHCenter)

        return grid_row + 1
