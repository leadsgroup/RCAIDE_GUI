import json
import os
import re
from collections.abc import Mapping
import numpy as np
import pyqtgraph as pg
# Shared application state. The Solve tab stores the latest mission results here.
import rcaide_io
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tabs import TabWidget

# RCAIDE parula palette anchors (deep blue → royal blue → teal → green)
_PLOT_COLORS = [
    (5,   104, 223),   # royal blue
    (19,  169, 200),   # teal
    (94,  201, 98),    # green
    (251, 189, 8),     # yellow
    (180, 80,  180),   # purple
]



#  Results Viewer Tab
class ResultsViewerWidget(TabWidget):
    """
    Browses rcaide_io.rcaide_results (mission simulation) or
    rcaide_io.last_performance_result (latest Performance tab analysis).
    The active source is chosen from a combo box; all tree, search, copy,
    export, and plot capabilities work on whichever object is loaded.
    """

    _PATH_ROLE = Qt.ItemDataRole.UserRole
    _POPULATED_ROLE = Qt.ItemDataRole.UserRole + 1

    # Source identifiers used internally
    _SRC_MISSION     = "Mission Results"
    _SRC_PERFORMANCE = "Performance Analysis"

    def __init__(self):
        super().__init__()

        # ----------------------------------------------
        # Internal viewer state
        # ----------------------------------------------
        self._nodes = {}
        self._root_data = None
        self._loaded_object_id = None
        self._search_node_limit = 5000
        self._active_path = None
        self._active_value = None
        # Root name used in path expressions (changes with source)
        self._root_name = "rcaide_results"

        # ----------------------------------------------
        # Layout
        # ----------------------------------------------
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # ----------------------------------------------
        # Title
        # ----------------------------------------------
        title = QLabel("Results Viewer")
        title.setFixedHeight(26)
        title.setStyleSheet("""
        QLabel {
            color: #9fb8ff;
            background: transparent;
            padding-left: 4px;
            font-size: 18px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        """)
        layout.addWidget(title)

        # ----------------------------------------------
        # Source selector row
        # ----------------------------------------------
        source_row = QHBoxLayout()
        source_row.setSpacing(8)
        source_row.addWidget(QLabel("Source:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems([self._SRC_MISSION, self._SRC_PERFORMANCE])
        self.source_combo.setFixedWidth(220)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        source_row.addWidget(self.source_combo)
        # Dynamic label shows the analysis name when performance source is active
        self.source_detail_label = QLabel("")
        self.source_detail_label.setStyleSheet("color: #7a94cc; font-size: 12px;")
        source_row.addWidget(self.source_detail_label)
        source_row.addStretch()
        layout.addLayout(source_row)

        # ----------------------------------------------
        # Action toolbar
        # ----------------------------------------------
        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Reload the selected source.")
        self.refresh_button.clicked.connect(lambda: self.refresh_from_values(force=True))
        controls.addWidget(self.refresh_button)

        # Copies the exact tree/path expression for later use in code or notes.
        self.copy_path_button = QPushButton("Copy Shown Path")
        self.copy_path_button.setToolTip("Copy the result path currently shown in the details pane.")
        self.copy_path_button.clicked.connect(self.copy_selected_path)
        controls.addWidget(self.copy_path_button)

        # Copies the inspected value itself, useful for quick debugging or reports.
        self.copy_value_button = QPushButton("Copy Shown Value")
        self.copy_value_button.setToolTip("Copy the value currently shown in the details pane.")
        self.copy_value_button.clicked.connect(self.copy_selected_value)
        controls.addWidget(self.copy_value_button)

        # Exports only the currently shown result branch/value.
        self.export_selected_button = QPushButton("Export Shown")
        self.export_selected_button.setToolTip("Save the currently shown value as JSON, and CSV when it is a numeric array.")
        self.export_selected_button.clicked.connect(self.export_selected)
        controls.addWidget(self.export_selected_button)

        # Exports the full stored results object and numeric leaf arrays.
        self.export_all_button = QPushButton("Export All")
        self.export_all_button.setToolTip("Save the full results object as JSON plus CSV files for numeric leaf arrays.")
        self.export_all_button.clicked.connect(self.export_all)
        controls.addWidget(self.export_all_button)

        # Search filters field names, paths, types, and previews in the left tree.
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search fields: altitude, velocity, mass, lift, throttle...")
        self.search_input.textChanged.connect(self.filter_tree)
        controls.addWidget(self.search_input, 1)

        layout.addLayout(controls)

        # ----------------------------------------------
        # Direct path inspector
        # ----------------------------------------------
        # Lets a user paste or type a MATLAB-style path instead of expanding the
        # tree manually to reach deeply nested arrays.
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Inspect path, e.g. rcaide_results.segments[0].conditions.freestream.altitude")
        self.path_input.returnPressed.connect(self.inspect_path)
        path_row.addWidget(self.path_input, 1)
        self.inspect_button = QPushButton("Inspect Path")
        self.inspect_button.setToolTip("Evaluate the typed result path and show that value on the right.")
        self.inspect_button.clicked.connect(self.inspect_path)
        path_row.addWidget(self.inspect_button)
        layout.addLayout(path_row)

        # ----------------------------------------------
        # Status/help line
        # ----------------------------------------------
        # Shows lightweight feedback for copy/export/search/path actions.
        self.status_label = QLabel("Select a tree row or inspect a path; copy/export buttons use the value shown on the right.")
        self.status_label.setFixedHeight(22)
        self.status_label.setStyleSheet("color: #b8c7d9; padding-left: 4px;")
        layout.addWidget(self.status_label)

        # ----------------------------------------------
        # Main split view
        # ----------------------------------------------
        # Left side: tree browser. Right side: selected path, text preview, and
        # optional numeric table preview.
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

        # Tree columns show the field name, type/shape, and a short value preview
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Name", "Class / Size", "Value"])
        self.tree.itemExpanded.connect(self.populate_item_children)
        self.tree.currentItemChanged.connect(self.show_item_details)
        header = self.tree.header()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        splitter.addWidget(self.tree)

        # Right-side details panel for the currently selected or inspected value.
        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(10, 0, 0, 0)
        details_layout.setSpacing(8)

        # Displays the exact path that copy/export actions will use.
        self.path_label = QLabel("No results loaded.")
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.path_label.setWordWrap(True)
        details_layout.addWidget(self.path_label)

        # Text preview for scalars, objects, mappings, and array summaries.
        self.value_preview = QTextEdit()
        self.value_preview.setReadOnly(True)
        self.value_preview.setMinimumHeight(120)
        details_layout.addWidget(self.value_preview, 1)

        # Spreadsheet-like preview for 1-D and 2-D numeric arrays.
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setVisible(False)
        details_layout.addWidget(self.table, 2)

        # ------ plot controls ------
        plot_ctrl_row = QHBoxLayout()
        plot_ctrl_row.setSpacing(6)
        plot_ctrl_row.addWidget(QLabel("X axis:"))
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.addItems(["Time (s)", "Range (m)", "Altitude (m)", "Mach", "Index"])
        self.x_axis_combo.setFixedWidth(130)
        plot_ctrl_row.addWidget(self.x_axis_combo)
        self.plot_button = QPushButton("Plot")
        self.plot_button.setEnabled(False)
        self.plot_button.setToolTip("Plot the selected array vs the chosen X axis.")
        self.plot_button.clicked.connect(self._plot_selected)
        plot_ctrl_row.addWidget(self.plot_button)
        self.add_to_plot_button = QPushButton("Add")
        self.add_to_plot_button.setEnabled(False)
        self.add_to_plot_button.setToolTip("Overlay the selected array on the existing plot.")
        self.add_to_plot_button.clicked.connect(lambda: self._plot_selected(overlay=True))
        plot_ctrl_row.addWidget(self.add_to_plot_button)
        self.clear_plot_button = QPushButton("Clear Plot")
        self.clear_plot_button.setEnabled(False)
        self.clear_plot_button.clicked.connect(self._clear_plot)
        plot_ctrl_row.addWidget(self.clear_plot_button)
        plot_ctrl_row.addStretch()
        details_layout.addLayout(plot_ctrl_row)

        # pyqtgraph PlotWidget — hidden until first Plot action.
        self.plot_widget = pg.PlotWidget()
        self._style_plot_widget(self.plot_widget)
        self.plot_widget.setMinimumHeight(200)
        self.plot_widget.setVisible(False)
        self._plot_series_count = 0   # tracks overlay count for color cycling
        details_layout.addWidget(self.plot_widget, 3)

        splitter.addWidget(details)
        splitter.setSizes([560, 640])

        # Populate from any mission results that already exist when the tab is created.
        self.refresh_from_values()


    def update_layout(self):
        # Called when the user switches to this tab; refresh in case results changed.
        self.refresh_from_values()

    def load_from_values(self):
        # Called by the app-wide load flow; keeps this tab aligned with shared state.
        self.refresh_from_values()

    # ----------------------------
    #  Source selection
    # ----------------------------
    def _on_source_changed(self):
        self.refresh_from_values(force=True)

    def _active_source(self):
        """Return (results_object, root_name, detail_text) for the chosen source."""
        src = self.source_combo.currentText()
        if src == self._SRC_PERFORMANCE:
            result = getattr(rcaide_io, "last_performance_result", None)
            label  = getattr(rcaide_io, "last_performance_label", "")
            return result, "performance_result", label
        else:
            result = getattr(rcaide_io, "rcaide_results", None)
            return result, "rcaide_results", ""

    # ----------------------------
    #  Results loading / refresh
    # ----------------------------
    def refresh_from_values(self, force=False):
        results, root_name, detail = self._active_source()
        object_id = id(results) if results is not None else None

        # Update the detail label (analysis name) regardless of reload decision
        self.source_detail_label.setText(f"— {detail}" if detail else "")

        if not force and object_id == self._loaded_object_id and root_name == self._root_name:
            return
        if force and object_id == self._loaded_object_id and root_name == self._root_name:
            self._set_status("Already showing the latest results.")
            return
        self._root_name = root_name
        self.load_results(results, root_name)

    def load_results(self, results, source_name="rcaide_results"):
        # Reset all UI/object caches before loading a new results object.
        self.tree.clear()
        self._nodes = {}
        self._root_data = results
        self._root_name = source_name
        self._loaded_object_id = id(results) if results is not None else None
        self._active_path = None
        self._active_value = None
        self.table.clear()
        self.table.setVisible(False)
        self._clear_plot()

        src = self.source_combo.currentText()
        if results is None:
            if src == self._SRC_PERFORMANCE:
                msg = "No performance analysis results yet. Run an analysis in the Performance tab first."
                hint = "Run an analysis in the Performance tab, then refresh here."
            else:
                msg = "No mission results loaded yet."
                hint = "Run a mission simulation, then come back here to browse the full results object."
            self.path_label.setText(msg)
            self.value_preview.setPlainText(hint)
            self._set_status("No results loaded.", clear_after_ms=0)
            return

        root = self._make_item(source_name, results, source_name)
        self.tree.addTopLevelItem(root)
        self._add_placeholder_if_needed(root, results)
        root.setExpanded(True)
        self.populate_item_children(root)
        self.tree.setCurrentItem(root)
        self._set_status(f"Loaded: {source_name}")

    # ------------------------------
    #  Tree expansion and selection
    # ------------------------------
    def populate_item_children(self, item):
        if item is None or item.data(0, self._POPULATED_ROLE):
            return

        path = item.data(0, self._PATH_ROLE)
        value = self._nodes.get(path)
        item.takeChildren()

        # Children are generated only when the user expands a node, which keeps
        # mission-sized result objects responsive.
        for child_name, child_value in self._iter_children(value):
            child_path = self._join_path(path, child_name)
            child = self._make_item(str(child_name), child_value, child_path)
            item.addChild(child)
            self._add_placeholder_if_needed(child, child_value)

        item.setData(0, self._POPULATED_ROLE, True)

    def show_item_details(self, current, _previous=None):
        # When a tree row is selected, show that exact value in the right pane.
        if current is None:
            return
        path = current.data(0, self._PATH_ROLE)
        value = self._nodes.get(path)
        self._show_value(path, value)

    # ------------------------------------------------------------------------------------------------------------------
    #  Direct path inspection
    # ------------------------------------------------------------------------------------------------------------------
    def inspect_path(self):
        # Let users paste/type a MATLAB-like path instead of manually expanding
        # the tree to reach a deeply nested result value.
        expression = self.path_input.text().strip()
        if not expression:
            self._set_status("Enter a results path to inspect.")
            return
        try:
            path, value = self._resolve_expression(expression)
        except Exception as exc:
            self._set_status(f"Could not resolve path: {exc}", clear_after_ms=8000)
            return
        self._show_value(path, value)
        self._set_status(f"Inspecting {path}")
        if path in self._nodes:
            item = self._find_item_by_path(path)
            if item is not None:
                self.tree.setCurrentItem(item)

    # ------------------------------------------------------------------------------------------------------------------
    #  Copy and export actions
    # ------------------------------------------------------------------------------------------------------------------
    def copy_selected_path(self):
        path = self._current_path()
        if not path:
            self._set_status("Nothing to copy yet. Select a tree row or inspect a path first.", clear_after_ms=8000)
            return
        QGuiApplication.clipboard().setText(path)
        self._set_status(f"Copied shown path to clipboard: {path}", clear_after_ms=8000)

    def copy_selected_value(self):
        path, value = self._current_value()
        if path is None:
            self._set_status("Nothing to copy yet. Select a tree row or inspect a path first.", clear_after_ms=8000)
            return
        QGuiApplication.clipboard().setText(self._copy_text(value))
        self._set_status(f"Copied shown value to clipboard from {path}.", clear_after_ms=8000)

    def export_selected(self):
        path, value = self._current_value()
        if path is None:
            self._set_status("Nothing to export yet. Select a tree row or inspect a path first.", clear_after_ms=8000)
            return
        export_dir = self._choose_export_dir()
        if not export_dir:
            self._set_status("Export cancelled.")
            return
        written = self._export_value(export_dir, path, value)
        self._set_status(f"Exported {len(written)} file(s) to {export_dir}.")

    def export_all(self):
        results = self._root_data
        if results is None:
            self._set_status("No results loaded.")
            return
        export_dir = self._choose_export_dir()
        if not export_dir:
            self._set_status("Export cancelled.")
            return
        written = self._export_value(export_dir, self._root_name, results)
        self._export_numeric_leaves(export_dir, self._root_name, results, written)
        self._set_status(f"Exported {len(written)} file(s) to {export_dir}.")

    # ------------------------------------------------------------------------------------------------------------------
    #  Search/filtering
    # ------------------------------------------------------------------------------------------------------------------
    def filter_tree(self, text):
        # Search expands a bounded number of nodes so nested fields can be found
        # without forcing the entire results object into the tree.
        needle = text.strip().lower()
        if needle:
            for index in range(self.tree.topLevelItemCount()):
                self._populate_descendants(
                    self.tree.topLevelItem(index),
                    max_nodes=self._search_node_limit,
                    include_array_items=False,
                )

        def apply_filter(item):
            path = str(item.data(0, self._PATH_ROLE)).lower()
            direct_match = (
                not needle
                or needle in path
                or needle in item.text(0).lower()
                or needle in item.text(1).lower()
                or needle in item.text(2).lower()
            )
            child_match = False
            for child_index in range(item.childCount()):
                child_match = apply_filter(item.child(child_index)) or child_match
            item.setHidden(not (direct_match or child_match))
            if needle and child_match:
                item.setExpanded(True)
            return direct_match or child_match

        for index in range(self.tree.topLevelItemCount()):
            apply_filter(self.tree.topLevelItem(index))

        self._set_status("Search cleared." if not needle else f"Search found {self._visible_item_count()} visible nodes.")

    # ------------------------------------------------------------------------------------------------------------------
    #  Current value tracking
    # ------------------------------------------------------------------------------------------------------------------
    def _show_value(self, path, value):
        # The details pane is the source of truth for copy/export. This avoids
        # confusion when a typed path and the tree selection differ.
        self._active_path = path
        self._active_value = value
        self.path_label.setText(path)
        self.path_input.setText(path)
        self.value_preview.setPlainText(self._detail_text(value))
        self._populate_table(value)
        self._update_plot_controls(value)

    def _current_path(self):
        return self._active_path

    def _current_value(self):
        if not self._active_path:
            return None, None
        return self._active_path, self._active_value

    # ------------------------------------------------------------------------------------------------------------------
    #  Path parsing and object navigation
    # ------------------------------------------------------------------------------------------------------------------
    def _resolve_expression(self, expression):
        # Resolve dotted/bracket paths against the currently loaded results object.
        # Strips either known root prefix so typed paths work regardless of source.
        expression = expression.strip()
        for prefix in ("rcaide_results", "performance_result", self._root_name):
            if expression.startswith(prefix):
                expression = expression[len(prefix):]
                break
        if expression.startswith("."):
            expression = expression[1:]

        value = self._root_data
        path = self._root_name
        if value is None:
            raise ValueError("no results object is loaded")
        for token in self._parse_tokens(expression):
            value = self._get_child(value, token)
            path = self._join_path(path, f"[{token}]" if isinstance(token, int) else token)
        return path, value

    def _parse_tokens(self, expression):
        # Convert "segments.cruise.conditions[0]" into tokens that _get_child
        # can apply to mappings, RCAIDE Data objects, lists, and arrays.
        tokens = []
        index = 0
        while index < len(expression):
            char = expression[index]
            if char == ".":
                index += 1
                continue
            if char == "[":
                end = expression.find("]", index)
                if end == -1:
                    raise ValueError("missing closing bracket")
                raw = expression[index + 1:end].strip()
                if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
                    tokens.append(raw[1:-1])
                else:
                    tokens.append(int(raw))
                index = end + 1
                continue
            match = re.match(r"[A-Za-z_][A-Za-z0-9_]*", expression[index:])
            if not match:
                raise ValueError(f"unexpected token near {expression[index:]!r}")
            tokens.append(match.group(0))
            index += len(match.group(0))
        return tokens

    def _get_child(self, value, token):
        # RCAIDE Data containers act like mappings, but some nested values are
        # plain objects, lists, tuples, or NumPy arrays. Handle each form.
        if self._is_mapping(value):
            if token in value:
                return value[token]
            if isinstance(token, int):
                try:
                    return value[token]
                except Exception:
                    items = [item_value for _item_key, item_value in value.items()]
                    return items[token]
            raise KeyError(token)
        if isinstance(value, np.ndarray):
            return value[token]
        if isinstance(value, (list, tuple)):
            return value[token]
        if isinstance(token, str) and hasattr(value, token):
            return getattr(value, token)
        return value[token]

    # ------------------------------------------------------------------------------------------------------------------
    #  Tree traversal helpers
    # ------------------------------------------------------------------------------------------------------------------
    def _populate_descendants(self, item, max_nodes=1000, include_array_items=True):
        # Iterative traversal avoids recursion depth issues on deeply nested results.
        count = 0
        stack = [item]
        while stack and count < max_nodes:
            current = stack.pop()
            path = current.data(0, self._PATH_ROLE)
            value = self._nodes.get(path)
            if not include_array_items and self._is_large_sequence(value):
                continue
            self.populate_item_children(current)
            count += 1
            for index in reversed(range(current.childCount())):
                stack.append(current.child(index))
        return count

    def _find_item_by_path(self, path):
        # Used after direct path inspection to sync the tree selection when the
        # inspected value is already present in the lazy-loaded tree.
        stack = [self.tree.topLevelItem(index) for index in range(self.tree.topLevelItemCount())]
        while stack:
            item = stack.pop()
            if item is not None and item.data(0, self._PATH_ROLE) == path:
                return item
            for index in range(item.childCount()):
                stack.append(item.child(index))
        return None

    def _visible_item_count(self):
        # Counts visible nodes after filtering for a useful search status message.
        count = 0
        stack = [self.tree.topLevelItem(index) for index in range(self.tree.topLevelItemCount())]
        while stack:
            item = stack.pop()
            if item is not None and not item.isHidden():
                count += 1
                for index in range(item.childCount()):
                    stack.append(item.child(index))
        return count

    # ------------------------------------------------------------------------------------------------------------------
    #  Status and export helpers
    # ------------------------------------------------------------------------------------------------------------------
    def _set_status(self, message, clear_after_ms=5000):
        # Temporary feedback for copy/export/search actions.
        self.status_label.setText(message)
        if clear_after_ms:
            QTimer.singleShot(clear_after_ms, lambda: self.status_label.setText(""))

    def _choose_export_dir(self):
        # Shared folder picker used by both export buttons.
        return QFileDialog.getExistingDirectory(self, "Choose Folder to Export Results", os.getcwd())

    def _export_value(self, export_dir, path, value):
        # Always write JSON for the selected branch/value. If the value is a
        # numeric vector/matrix, also write a CSV for MATLAB/Excel/Python use.
        os.makedirs(export_dir, exist_ok=True)
        written = []
        base_name = self._safe_filename(path)
        json_path = os.path.join(export_dir, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(self._json_safe(value), file, indent=2)
        written.append(json_path)

        arr = self._array_for_export(value)
        if arr is not None:
            csv_path = os.path.join(export_dir, f"{base_name}.csv")
            np.savetxt(csv_path, arr, delimiter=",", fmt="%s")
            written.append(csv_path)
        return written

    def _export_numeric_leaves(self, export_dir, path, value, written, limit=200):
        # Export All walks the object and writes CSVs for numeric leaf arrays,
        # capped so a very large mission cannot create unlimited files.
        if len(written) >= limit:
            return
        if self._is_mapping(value):
            for key, child in self._sorted_mapping_items(value):
                self._export_numeric_leaves(export_dir, self._join_path(path, key), child, written, limit)
            return
        if isinstance(value, (list, tuple)) and not self._is_numeric_table(value):
            for index, child in enumerate(value):
                self._export_numeric_leaves(export_dir, f"{path}[{index}]", child, written, limit)
            return

        arr = self._array_for_export(value)
        if arr is None:
            return
        csv_path = os.path.join(export_dir, f"{self._safe_filename(path)}.csv")
        np.savetxt(csv_path, arr, delimiter=",", fmt="%s")
        written.append(csv_path)

    def _array_for_export(self, value):
        # Only 1-D and 2-D numeric data maps cleanly to CSV.
        try:
            arr = np.asarray(value)
        except Exception:
            return None
        if arr.ndim == 0 or arr.size == 0 or arr.dtype.kind not in "biufc":
            return None
        if arr.ndim == 1:
            return arr.reshape((-1, 1))
        if arr.ndim == 2:
            return arr
        return None

    def _json_safe(self, value):
        # Convert RCAIDE/NumPy values to JSON-friendly structures.
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        if self._is_mapping(value):
            return {str(key): self._json_safe(child) for key, child in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._json_safe(child) for child in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def _safe_filename(self, path):
        # Use the result path as the filename, but strip characters unsafe for Windows paths.
        text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(path)).strip("_")
        return text[:180] or "result"

    # ------------------------------------------------------------------------------------------------------------------
    #  Tree item creation and child discovery
    # ------------------------------------------------------------------------------------------------------------------
    def _make_item(self, name, value, path):
        # Store the live Python object by path so selecting a tree row can show
        # the real RCAIDE value without serializing the whole results structure.
        self._nodes[path] = value
        item = QTreeWidgetItem([name, self._type_text(value), self._preview_text(value)])
        item.setData(0, self._PATH_ROLE, path)
        item.setData(0, self._POPULATED_ROLE, False)
        return item

    def _add_placeholder_if_needed(self, item, value):
        # Placeholder creates the expansion arrow before children are actually loaded.
        if self._has_children(value):
            item.addChild(QTreeWidgetItem(["Loading...", "", ""]))

    def _has_children(self, value):
        # Scalars and small numeric tables are terminal leaves; containers can expand.
        if self._is_mapping(value):
            return bool(list(value.keys()))
        if isinstance(value, np.ndarray):
            return value.ndim > 2
        if isinstance(value, (list, tuple)):
            return bool(value) and not self._is_numeric_table(value)
        return False

    def _iter_children(self, value):
        # Yield display-name/value pairs for the supported container types.
        if self._is_mapping(value):
            for key, child in self._sorted_mapping_items(value):
                yield str(key), child
            return
        if isinstance(value, np.ndarray) and value.ndim > 2:
            for index, child in enumerate(value):
                yield f"[{index}, :]", child
            return
        if isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                yield f"[{index}]", child

    # ------------------------------------------------------------------------------------------------------------------
    #  Type, path, and preview formatting
    # ------------------------------------------------------------------------------------------------------------------
    def _is_mapping(self, value):
        # RCAIDE Data containers provide items(); Mapping covers normal dicts.
        return isinstance(value, Mapping) or (hasattr(value, "items") and callable(value.items))

    def _sorted_mapping_items(self, value):
        # Put the result fields users usually care about near the top.
        items = list(value.items())
        priority = {
            "segments": 0,
            "conditions": 1,
            "frames": 2,
            "inertial": 3,
            "freestream": 4,
            "aerodynamics": 5,
            "weights": 6,
            "propulsion": 7,
            "energy": 8,
            "tag": 99,
        }
        return sorted(items, key=lambda item: priority.get(str(item[0]), 20))

    def _join_path(self, parent, child):
        # Build readable paths such as rcaide_results.segments.cruise.conditions.
        child = str(child)
        if child.startswith("["):
            return f"{parent}{child}"
        return f"{parent}.{child}" if parent else child

    def _type_text(self, value):
        # Second tree column: class/type plus useful size information.
        if isinstance(value, np.ndarray):
            return f"ndarray {tuple(value.shape)}"
        if self._is_mapping(value):
            return f"{type(value).__name__} ({len(list(value.keys()))})"
        if isinstance(value, (list, tuple)):
            shape = self._list_shape(value)
            return f"{type(value).__name__} {shape}" if shape else f"{type(value).__name__} ({len(value)})"
        return type(value).__name__

    def _list_shape(self, value):
        # Infer simple nested-list shape for list-based numeric data.
        shape = []
        current = value
        while isinstance(current, (list, tuple)):
            shape.append(len(current))
            if not current:
                break
            current = current[0]
        return tuple(shape) if len(shape) > 1 else None

    def _preview_text(self, value):
        # Third tree column: compact value summary that avoids dumping huge arrays.
        if isinstance(value, np.ndarray):
            if value.size == 0:
                return "empty"
            return self._short_text(value.reshape(-1)[:6].tolist())
        if self._is_mapping(value):
            tag = self._mapping_get(value, "tag")
            if tag not in (None, ""):
                return f"tag: {tag}"
            return ", ".join(str(key) for key, _value in self._sorted_mapping_items(value)[:6])
        if isinstance(value, (list, tuple)):
            if self._is_numeric_table(value):
                return self._short_text(np.asarray(value).reshape(-1)[:6].tolist())
            return self._short_text(value[:6])
        return self._short_text(value)

    def _short_text(self, value, limit=140):
        # Clamp previews so the tree remains readable.
        text = repr(value)
        return text[: limit - 3] + "..." if len(text) > limit else text

    def _detail_text(self, value):
        # Right-pane text summary. Containers show fields; numeric values also
        # get shape/dtype plus a JSON-style preview.
        lines = [f"Class / size: {self._type_text(value)}"]
        summary = self._summary_lines(value)
        if summary:
            lines.extend(summary)
            return "\n".join(lines)

        if isinstance(value, np.ndarray):
            lines.append(f"Shape: {tuple(value.shape)}")
            lines.append(f"Dtype: {value.dtype}")
        elif isinstance(value, (list, tuple)) and self._is_numeric_table(value):
            arr = np.asarray(value)
            lines.append(f"Shape: {tuple(arr.shape)}")
            lines.append(f"Dtype: {arr.dtype}")
        lines.append("")
        lines.append(self._copy_text(value, limit=4000))
        return "\n".join(lines)

    def _summary_lines(self, value):
        # Human-readable summaries for mappings and non-numeric sequences.
        if self._is_mapping(value):
            keys = [str(key) for key in value.keys()]
            lines = [f"Fields: {len(keys)}"]
            tag = self._mapping_get(value, "tag")
            if tag not in (None, ""):
                lines.append(f"Tag: {tag}")
            useful = [
                key for key in (
                    "segments",
                    "conditions",
                    "frames",
                    "inertial",
                    "freestream",
                    "aerodynamics",
                    "weights",
                    "propulsion",
                    "energy",
                )
                if key in keys
            ]
            if useful:
                lines.append("Common result groups: " + ", ".join(useful))
            preview_keys = keys[:12]
            lines.append("")
            lines.append("Fields:")
            lines.extend(f"  {key}" for key in preview_keys)
            if len(keys) > len(preview_keys):
                lines.append(f"  ... {len(keys) - len(preview_keys)} more")
            return lines

        if isinstance(value, (list, tuple)) and not self._is_numeric_table(value):
            return [f"Items: {len(value)}", "", "Expand items in the tree to inspect nested result data."]

        return []

    def _copy_text(self, value, limit=None):
        # Clipboard/export preview text. JSON formatting is preferred when possible.
        if isinstance(value, np.ndarray):
            value = value.tolist()
        try:
            text = json.dumps(value, indent=2, default=str)
        except TypeError:
            text = repr(value)
        return text[:limit] + "\n..." if limit is not None and len(text) > limit else text

    def _is_numeric_table(self, value):
        # Recognizes values that can be shown as a simple table.
        try:
            arr = np.asarray(value)
        except Exception:
            return False
        return arr.ndim in (1, 2) and arr.size > 0 and arr.dtype.kind in "biufc"

    def _is_large_sequence(self, value):
        # Search avoids expanding large arrays unless the user explicitly expands them.
        if isinstance(value, np.ndarray):
            return value.size > 50
        if isinstance(value, (list, tuple)) and self._is_numeric_table(value):
            return len(value) > 50
        return False

    def _mapping_get(self, value, key, default=None):
        # Safe getter for dict-like RCAIDE Data objects.
        try:
            return value.get(key, default)
        except Exception:
            try:
                return value[key]
            except Exception:
                return default

    # ------------------------------------------------------------------------------------------------------------------
    #  Numeric table preview
    # ------------------------------------------------------------------------------------------------------------------
    def _populate_table(self, value):
        # Numeric vectors/matrices get a spreadsheet-like preview; larger or
        # higher-dimensional data remains available through copy/export.
        self.table.clear()
        if isinstance(value, np.ndarray):
            arr = value
        elif self._is_numeric_table(value):
            arr = np.asarray(value)
        else:
            self.table.setVisible(False)
            return

        if arr.ndim == 0:
            self.table.setVisible(False)
            return
        if arr.ndim == 1:
            arr = arr.reshape((-1, 1))
        if arr.ndim != 2:
            self.table.setVisible(False)
            return

        max_rows = min(arr.shape[0], 200)
        max_cols = min(arr.shape[1], 25)
        self.table.setRowCount(max_rows)
        self.table.setColumnCount(max_cols)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(max_cols)])
        self.table.setVerticalHeaderLabels([str(i) for i in range(max_rows)])
        self.table.setToolTip(f"Showing {max_rows} of {arr.shape[0]} rows and {max_cols} of {arr.shape[1]} columns.")

        for row in range(max_rows):
            for col in range(max_cols):
                self.table.setItem(row, col, QTableWidgetItem(str(arr[row, col])))

        self.table.setVisible(True)


    # ------------------------------------------------------------------------------------------------------------------
    #  Plot helpers
    # ------------------------------------------------------------------------------------------------------------------
    def _style_plot_widget(self, w):
        pi = w.getPlotItem()
        for axis_name in ("bottom", "left", "top", "right"):
            axis = pi.getAxis(axis_name)
            if axis is not None:
                axis.setPen(pg.mkPen("#4da3ff"))
                axis.setTextPen(pg.mkPen("#9fb8ff"))
        pi.getViewBox().setBorder(pg.mkPen("#1f2a36"))
        w.setBackground("#0a0f1a")

    def _update_plot_controls(self, value):
        can_plot = self._is_plottable_series(value)
        self.plot_button.setEnabled(can_plot)
        self.add_to_plot_button.setEnabled(can_plot and self.plot_widget.isVisible())

    def _is_plottable_series(self, value):
        if not isinstance(value, np.ndarray):
            return False
        if value.size < 2:
            return False
        if value.ndim == 1:
            return True
        if value.ndim == 2 and value.shape[1] == 1:
            return True
        return False

    def _segment_base_path(self, active_path):
        # Returns e.g. 'rcaide_results.segments.cruise' from a deeper conditions path.
        # Handles both dot-notation (named) and bracket-notation (indexed) segments.
        m = re.match(r'(rcaide_results\.segments(?:\.[^.\[]+|\[\d+\]))', active_path or "")
        return m.group(1) if m else None

    def _get_x_data(self, x_label):
        """Return (array_1d, label) for the chosen X axis, or (None, label) on failure."""
        seg_base = self._segment_base_path(self._active_path)
        if x_label == "Index" or seg_base is None:
            n = np.asarray(self._active_value).flatten().size
            return np.arange(n, dtype=float), "Index"

        _x_suffixes = {
            "Time (s)":     ".conditions.frames.inertial.time",
            "Range (m)":    ".conditions.frames.inertial.aircraft_range",
            "Altitude (m)": ".conditions.freestream.altitude",
            "Mach":         ".conditions.freestream.mach_number",
        }
        suffix = _x_suffixes.get(x_label)
        if suffix is None:
            n = np.asarray(self._active_value).flatten().size
            return np.arange(n, dtype=float), "Index"

        try:
            _, val = self._resolve_expression(seg_base + suffix)
            return np.asarray(val).flatten(), x_label
        except Exception:
            n = np.asarray(self._active_value).flatten().size
            return np.arange(n, dtype=float), "Index (X not found)"

    def _plot_selected(self, overlay=False):
        if not self._is_plottable_series(self._active_value):
            self._set_status("Select a numeric array first.", clear_after_ms=5000)
            return

        y = np.asarray(self._active_value).flatten()
        x_label = self.x_axis_combo.currentText()
        x, x_label_used = self._get_x_data(x_label)

        n = min(len(x), len(y))
        x, y = x[:n], y[:n]

        if not overlay:
            self.plot_widget.clear()
            self._plot_series_count = 0

        # addLegend() reuses the existing LegendItem if one already exists.
        legend = self.plot_widget.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(8, 12, 18, 180))
        legend.setPen(pg.mkPen(120, 150, 210, 140))

        color = _PLOT_COLORS[self._plot_series_count % len(_PLOT_COLORS)]
        self._plot_series_count += 1

        # Short label: last two dot-components of the path
        parts = (self._active_path or "").split(".")
        y_label = ".".join(parts[-2:]) if len(parts) >= 2 else parts[-1]

        self.plot_widget.plot(
            x, y,
            pen=pg.mkPen(color=color, width=2),
            name=y_label,
        )
        if not overlay:
            self.plot_widget.setLabel("left", y_label, color="white", size="12px")
        self.plot_widget.setLabel("bottom", x_label_used, color="white", size="12px")
        self.plot_widget.setVisible(True)
        self.clear_plot_button.setEnabled(True)
        self.add_to_plot_button.setEnabled(True)
        self._set_status(f"Plotted {self._active_path}")

    def _clear_plot(self):
        self.plot_widget.clear()
        self.plot_widget.setVisible(False)
        self.clear_plot_button.setEnabled(False)
        self.add_to_plot_button.setEnabled(False)
        self._plot_series_count = 0
        self._set_status("Plot cleared.")


def get_widget() -> QWidget:
    # Factory used by main.py when constructing the application tab list.
    return ResultsViewerWidget()
