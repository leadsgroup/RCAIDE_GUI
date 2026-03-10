from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QScrollArea, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy, QAbstractItemView
)

from tabs.mission.widgets import MissionSegmentWidget
from tabs.mission.widgets import MissionAnalysisWidget
from tabs import TabWidget
from tabs.aircraft_configs.aircraft_configs import AircraftConfigsWidget
import values
import RCAIDE

# ============================================================
#  Mission Profile (animated line diagram)
# ============================================================
class MissionProfileWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Constrain the profile card so it remains readable in compact layouts.
        self.setMinimumHeight(220)
        self.setMaximumHeight(320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Each phase entry is stored as (display_name, normalized_phase_type).
        self.phases = []
        # 0..1 progress used to animate the moving marker along the profile.
        self._progress = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_animation)
        # 25 FPS-ish update cadence for lightweight motion.
        self._timer.start(40)
        self.setAutoFillBackground(False)

    def set_phases(self, names):
        normalized = []
        for item in (names or []):
            if isinstance(item, tuple) and len(item) == 2:
                label, ptype = item
                label_text = str(label).title()
                # Re-classify using both type + label to avoid name-only misclassification.
                normalized.append((label_text, self._phase_type(f"{ptype} {label_text}")))
            else:
                text = str(item).title()
                normalized.append((text, self._phase_type(text)))
        self.phases = normalized
        # Restart marker animation whenever phases are regenerated.
        self._progress = 0.0
        self.update()

    def _advance_animation(self):
        if not self.phases or len(self.phases) < 2:
            return
        self._progress += 0.005
        if self._progress > 1.0:
            self._progress = 0.0
        self.update()

    @staticmethod
    def _phase_type(name):
        n = str(name).lower().replace("_", " ")
        # Prefer explicit phase prefix from overview tuples (stable and deterministic).
        if n.startswith("vertical climb"):
            return "vertical_climb"
        if n.startswith("vertical descent"):
            return "vertical_descent"
        if n.startswith("vertical hover"):
            return "vertical_hover"
        if n.startswith("single point"):
            return "single_point"
        if n.startswith("ground"):
            return "ground"
        if n.startswith("descent"):
            return "descent"
        if n.startswith("climb"):
            return "climb"
        if n.startswith("cruise"):
            return "cruise"
        if n.startswith("takeoff") or n.startswith("taxi"):
            return "takeoff"
        if "vertical" in n and "climb" in n:
            return "vertical_climb"
        if "vertical" in n and ("descent" in n or "descend" in n):
            return "vertical_descent"
        if "vertical" in n and "hover" in n:
            return "vertical_hover"
        if "single point" in n:
            return "single_point"
        if "ground" in n:
            return "ground"
        if "descent" in n or n.startswith("des"):
            return "descent"
        if "climb" in n:
            return "climb"
        if "cruise" in n:
            return "cruise"
        if "landing" in n or "land" in n or "approach" in n:
            return "landing"
        return "other"
    
    def _phase_color(self, ptype):
        colors = {
            "takeoff": "#4caf50",
            "climb": "#81c784",
            "cruise": "#64b5f6",
            "descent": "#ffb74d",
            "landing": "#e57373",
            "ground": "#8d6e63",
            "single_point": "#ab47bc",
            "vertical_climb": "#26a69a",
            "vertical_descent": "#26a69a",
            "vertical_hover": "#26a69a",
        }
        return QColor(colors.get(ptype, "#b0bec5"))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        outer = self.rect().adjusted(16, 14, -16, -14)
        # Keep vertical/horizontal proportions consistent for a less flattened profile.
        plot_h = int(outer.height() * 0.72)
        rect = outer.adjusted(0, 0, 0, -(outer.height() - plot_h))
        painter.fillRect(self.rect(), QColor("#050a12"))

        painter.setPen(QPen(QColor("#1f2933"), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = rect.top() + i * rect.height() / 4
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))

        if not self.phases:
            painter.setPen(QColor("#8c9aa8"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Mission profile will appear here once you add segments.",
            )
            return

        # Build a normalized altitude trace (0..1-ish in plot space) from phase types.
        n = len(self.phases)
        alt = []
        cur = 0.15
        for _, ptype in self.phases:
            if ptype in ("takeoff", "climb"):
                cur += 0.18
            elif ptype == "vertical_climb":
                cur += 0.24
            elif ptype == "cruise":
                cur += 0.0
            elif ptype in ("descent", "landing"):
                cur -= 0.18
            elif ptype == "vertical_descent":
                cur -= 0.24
            elif ptype == "ground":
                cur = 0.10
            elif ptype in ("single_point", "vertical_hover"):
                cur += 0.0
            else:
                cur += 0.05
            cur = max(0.08, min(0.85, cur))
            alt.append(cur)
        # Seed the first point so the first segment starts from a realistic state.
        first_ptype = self.phases[0][1] if self.phases else "other"
        if first_ptype in ("takeoff", "climb"):
            start_alt = 0.08
        elif first_ptype == "vertical_climb":
            # Ensure the first vertical climb draws as a visible segment, not a point.
            start_alt = 0.10
        elif first_ptype in ("descent", "landing", "vertical_descent"):
            start_alt = 0.78
        elif first_ptype == "ground":
            start_alt = 0.10
        elif first_ptype in ("single_point", "vertical_hover"):
            start_alt = alt[0] if alt else 0.45
        elif alt:
            start_alt = alt[0]
        else:
            start_alt = 0.08
        alt.insert(0, start_alt)

        # Uniform x-spacing across segments.
        dx = rect.width() / max(n, 1)
        xs = [rect.left() + i * dx for i in range(n + 1)]

        # Fixed runway-level y used for all ground segments.
        ground_y = rect.bottom() - 0.10 * rect.height()
        painter.setFont(QFont("Segoe UI", 8))
        for i, (name, ptype) in enumerate(self.phases):
            color = self._phase_color(ptype)
            x1, x2 = xs[i], xs[i + 1]
            y1 = rect.bottom() - alt[i] * rect.height()
            y2 = rect.bottom() - alt[i + 1] * rect.height()
            painter.setPen(QPen(color, 2.0))
            cx = 0.5 * (x1 + x2)
            if ptype == "ground":
                # Ground is always shown as a constant-altitude line near runway level.
                y1 = ground_y
                y2 = ground_y
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            elif ptype in ("vertical_climb", "vertical_descent", "vertical_hover"):
                # Vertical phases are represented by vertical motion in the same x-slot.
                painter.drawLine(QPointF(cx, y1), QPointF(cx, y2))
            elif ptype == "single_point":
                # Single-point phases are event markers instead of trajectory segments.
                py = y2
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QPointF(cx, py), 4.5, 4.5)
                painter.setBrush(Qt.BrushStyle.NoBrush)
            else:
                seg_path = QPainterPath()
                seg_path.moveTo(x1, y1)
                seg_path.lineTo(x2, y2)
                painter.drawPath(seg_path)

            label_y = max(min(y1, y2) - 16, rect.top() + 4)
            painter.setPen(QColor("#e8f2ff"))
            painter.drawText(
                int(cx - 55),
                int(label_y),
                110,
                18,
                Qt.AlignmentFlag.AlignCenter,
                name,
            )
        painter.setPen(QPen(QColor("#3f5670"), 1.2))
        painter.drawLine(
            int(rect.left()),
            int(rect.bottom()),
            int(rect.right()),
            int(rect.bottom()),
        )

        # Animate a marker over the currently active segment.
        total_segments = n
        t = self._progress * total_segments
        idx = int(t)
        frac = t - idx
        if idx >= total_segments:
            idx = total_segments - 1
            frac = 1.0

        x1, x2 = xs[idx], xs[idx + 1]
        seg_ptype = self.phases[idx][1]
        y1 = rect.bottom() - alt[idx] * rect.height()
        y2 = rect.bottom() - alt[idx + 1] * rect.height()
        # Keep the animated dot aligned with each segment's custom drawing rule.
        if seg_ptype == "ground":
            mx = x1 + (x2 - x1) * frac
            my = ground_y
        elif seg_ptype in ("vertical_climb", "vertical_descent", "vertical_hover"):
            mx = 0.5 * (x1 + x2)
            my = y1 + (y2 - y1) * frac
        elif seg_ptype == "single_point":
            mx = 0.5 * (x1 + x2)
            my = y2
        else:
            mx = x1 + (x2 - x1) * frac
            my = y1 + (y2 - y1) * frac
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(mx, my), 4, 4)
        painter.setPen(QPen(QColor("#64b5f6"), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(mx, my), 7, 7)

# ============================================================
#  Mission Summary Table
# ============================================================
class MissionSummaryTable(QTableWidget):
    def __init__(self, mission_widget):
        super().__init__(0, 6)
        # Parent mission widget reference for reading segment state and UI navigation.
        self.mission_widget = mission_widget

        # Table columns summarizing each segment's key mission/solver metadata.
        self.horizontalHeader().setMinimumSectionSize(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setHorizontalHeaderLabels(
            [
                "Segment",
                "Type",
                "Config",
                "Ctrl Pts",
                "Unknowns",
                "Residuals",
            ]
        )
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalHeader().setMinimumSectionSize(72)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.verticalHeader().setDefaultSectionSize(28)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        # Keep visual style consistent with the Mission tab theme.
        self.setStyleSheet(
            """
            QTableWidget {
                background-color:#060b13;
                color:#e5f0ff;
                border:1px solid #2d3a4e;
                font-size:13px;
                gridline-color:#23334b;
            }
            QHeaderView::section {
                background-color:#111b2d;
                color:#a8c6ff;
                font-weight:600;
                padding:3px;
            }
            QTableWidget::item:selected { background-color:#1b2a44; }
            """
        )
        # Clicking a row focuses/open the corresponding segment detail panel.
        self.cellClicked.connect(self._row_clicked)

    @staticmethod
    def _count_active(data):
        # Count active boolean-style entries stored as `(enabled, value)` tuples.
        if not isinstance(data, dict):
            return 0
        total = 0
        for value in data.values():
            if isinstance(value, tuple) and value and bool(value[0]):
                total += 1
        return total

    @staticmethod
    def _norm(name):
        # Normalize config names for robust dictionary/list matching.
        return str(name or "").strip().lower().replace(" ", "_")

    def update_table(self):
        # Rebuild the full table from current segment widgets.
        segs = self.mission_widget.segment_widgets
        if not segs and self.mission_widget.tree.topLevelItemCount() > 0:
            # Tree exists but detail widgets are not yet available (loading/rebuild state).
            self.clearSpans()
            self.clearContents()
            self.setRowCount(self.mission_widget.tree.topLevelItemCount())
            for r in range(self.mission_widget.tree.topLevelItemCount()):
                name = self.mission_widget.tree.topLevelItem(r).text(0)
                values_row = [name, "-", "-", "-", "-", "-"]
                for c, val in enumerate(values_row):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setItem(r, c, item)
            row_h = self.rowHeight(0) if self.rowCount() else 26
            visible_rows = max(4, min(self.rowCount(), 8))
            self.setMinimumHeight(self.horizontalHeader().height() + (row_h * visible_rows) + 10)
            return

        if not segs:
            # Explicit empty state before any segments are added.
            self.clearContents()
            self.setRowCount(1)
            item = QTableWidgetItem("No segments added yet.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(0, 0, item)
            self.setSpan(0, 0, 1, 6)
            row_h = max(self.rowHeight(0), 26)
            self.setMinimumHeight(self.horizontalHeader().height() + (row_h * 4) + 10)
            return

        rows = []
        for idx, seg in enumerate(segs):
            # Resolve display name with fallback to tree text and generated default.
            name = seg.segment_name_input.text().strip() if hasattr(seg, "segment_name_input") else ""
            if not name and idx < self.mission_widget.tree.topLevelItemCount():
                name = self.mission_widget.tree.topLevelItem(idx).text(0)
            if not name:
                name = f"Segment {idx + 1}"
            sub_type = seg.nested_dropdown.currentText() if hasattr(seg, "nested_dropdown") else "Custom"
            if sub_type == "Constant Speed/Constant Altitude":
                sub_type = "Const Spd/Alt"
            # Resolve config from selector text first, then index-based fallbacks.
            config_name = ""
            if hasattr(seg, "config_selector"):
                config_name = seg.config_selector.currentText().strip()
                if not config_name:
                    cfg_idx = seg.config_selector.currentIndex()
                    if cfg_idx >= 0:
                        config_name = seg.config_selector.itemText(cfg_idx).strip()
                    if not config_name and isinstance(values.config_data, list) and 0 <= cfg_idx < len(values.config_data):
                        cfg = values.config_data[cfg_idx]
                        if isinstance(cfg, dict):
                            config_name = str(cfg.get("config name", "")).strip()
                    if not config_name:
                        cfgs = getattr(values, "rcaide_configs", None)
                        if isinstance(cfgs, dict) and cfg_idx >= 0:
                            keys = list(cfgs.keys())
                            if cfg_idx < len(keys):
                                config_name = str(keys[cfg_idx]).strip()
            if not config_name and hasattr(seg, "_default_config_key"):
                try:
                    # Final fallback: infer config from segment semantics.
                    cfg_key = seg._default_config_key(
                        seg.top_dropdown.currentText() if hasattr(seg, "top_dropdown") else "",
                        seg.nested_dropdown.currentText() if hasattr(seg, "nested_dropdown") else "",
                        name,
                    )
                    if isinstance(values.config_data, list):
                        for cfg in values.config_data:
                            if isinstance(cfg, dict):
                                cfg_name = str(cfg.get("config name", "")).strip()
                                if self._norm(cfg_name) == self._norm(cfg_key):
                                    config_name = cfg_name
                                    break
                    if not config_name:
                        cfgs = getattr(values, "rcaide_configs", None)
                        if isinstance(cfgs, dict):
                            for key in cfgs.keys():
                                if self._norm(key) == self._norm(cfg_key):
                                    config_name = str(key)
                                    break
                except Exception:
                    pass
            if not config_name:
                config_name = "Base"
            cp = seg.ctrl_points.text().strip() if hasattr(seg, "ctrl_points") else "16"
            # Unknowns/residuals are active-control and active-force counts.
            controls_data = {}
            if hasattr(seg, "flight_controls_widget") and seg.flight_controls_widget:
                try:
                    controls_data = seg.flight_controls_widget.get_data()
                except Exception:
                    controls_data = {}
            forces_data = {}
            if hasattr(seg, "dof_entry_widget") and seg.dof_entry_widget:
                try:
                    forces_data = seg.dof_entry_widget.get_values()
                except Exception:
                    forces_data = {}
            unknowns = self._count_active(controls_data)
            residuals = self._count_active(forces_data)
            # Keep takeoff/ground rows grouped first for quick scan.
            is_takeoff = "takeoff" in name.lower() or "ground" in str(sub_type).lower()
            rows.append((is_takeoff, idx, name, sub_type, config_name, cp, unknowns, residuals))

        rows.sort(key=lambda r: (not r[0], r[1]))
        self.clearSpans()
        self.clearContents()
        self.setRowCount(len(rows))

        for r, (_, seg_idx, name, sub_type, config_name, cp, unknowns, residuals) in enumerate(rows):
            values_row = [name, sub_type, config_name, cp, unknowns, residuals]
            for c, val in enumerate(values_row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setToolTip(str(val))
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, seg_idx)
                self.setItem(r, c, item)

        self.resizeRowsToContents()
        row_h = self.rowHeight(0) if rows else 26
        visible_rows = max(4, min(len(rows), 8))
        self.setMinimumHeight(self.horizontalHeader().height() + (row_h * visible_rows) + 10)

    def _row_clicked(self, row, col):
        # Navigate from summary row to the matching collapsible details panel.
        item = self.item(row, 0)
        if item is None:
            return
        seg_index = item.data(Qt.ItemDataRole.UserRole)
        if seg_index is None:
            return

        panel_index = int(seg_index) * 2
        layout = self.mission_widget.details_layout
        if panel_index < layout.count():
            widget = layout.itemAt(panel_index).widget()
            if hasattr(widget, "toggle") and not getattr(widget, "is_open", True):
                widget.toggle()
            self.mission_widget.details_scroll.ensureWidgetVisible(widget)

# ============================================================
#  Collapsible Panel wrapper
# ============================================================
class CollapsiblePanel(QWidget):
    """A small panel with a header button that toggles visibility of content.
    - title: display title for the header button
    - content_widget: the QWidget that will be shown/hidden when toggled
    """

    def __init__(self, title: str, content_widget: QWidget):
        super().__init__()

        # Track whether the panel is currently expanded
        self.is_open = True

        # The widget that will be shown or hidden
        self.content = content_widget

        # Button that acts as the collapsible panel header
        self.toggle_btn = QPushButton(f"▼  {title}")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)

        # Connect button click to expand/collapse behavior
        self.toggle_btn.clicked.connect(self.toggle)

        # Visual styling for the header button
        # (kept as a raw stylesheet string to preserve look-and-feel)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d1522;
                border: 1px solid #2d3a4e;
                border-radius: 6px;
                padding: 6px;
                color: #e5f0ff;
                text-align: left;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:checked { background-color: #162234; }
        """)

        # Vertical layout: header button on top, content below
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.content)

    def toggle(self):
        """Flip the panel open/closed and update the header arrow."""
        # Toggle open/closed state
        self.is_open = not self.is_open

        # Show or hide the content widget
        self.content.setVisible(self.is_open)

        # Update arrow icon in the header text (preserve the existing title)
        self.toggle_btn.setText(
            f"{'▼' if self.is_open else '►'}  {self.toggle_btn.text()[2:]}"
        )

# ===================================
#  Mission Widget (Main Tab)
# ===================================
class MissionWidget(TabWidget):
    """Main mission tab widget used in the application's tab view.
    Includes:
    - Allowing the user to create and manage mission segments
    - Displaying segment details in collapsible panels
    - Saving/loading mission data to/from the global `values` object
    - Interacting with RCAIDE mission objects when saving
    """

    def __init__(self, shared_analysis_widget=None):
        super().__init__()


        # List of MissionSegmentWidget instances currently in the mission
        self.segment_widgets = []
        # Indices of segments that have been disabled by the user
        self.disabled_segments = set()

        main_layout = QVBoxLayout(self)

        left_col = QWidget()
        left_v = QVBoxLayout(left_col)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(8)

        right_col = QWidget()
        right_v = QVBoxLayout(right_col)
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.setSpacing(8)

        segments_box = QGroupBox("Mission Setup")
        segments_v = QVBoxLayout(segments_box)

        # Small notice label
        self.segment_notice = QLabel("")
        self.segment_notice.setVisible(False)
        self.segment_notice.setStyleSheet("""
            QLabel {
                color:#8fd3ff;
                background:#0d223a;
                border:1px solid #1f6feb;
                border-radius:4px;
                padding:4px 8px;
            }
        """)
        segments_v.addWidget(self.segment_notice)

        # Row: mission name input
        name_row = QHBoxLayout()
        name_label = QLabel("Segment Name:")
        name_label.setStyleSheet("color:#dbe7ff;")
        self.mission_name_input = QLineEdit()
        self.mission_name_input.setPlaceholderText("Enter mission name...")
        name_row.addWidget(name_label)
        name_row.addWidget(self.mission_name_input)
        segments_v.addLayout(name_row)

        # Row: action buttons (add segment, save data)
        btn_row = QHBoxLayout()
        self.add_segment_btn = QPushButton("➕ Add Segment")
        self.save_btn = QPushButton("💾 Save All Data")
        for b in (self.add_segment_btn, self.save_btn):
            b.setStyleSheet("background-color:#141b29; color:#e5f0ff;")

        # Wire button clicks to handler methods (no logic change)
        self.add_segment_btn.clicked.connect(self.add_segment)
        self.save_btn.clicked.connect(self.save_all_data)

        btn_row.addWidget(self.add_segment_btn)
        btn_row.addWidget(self.save_btn)
        segments_v.addLayout(btn_row)

        # Tree widget to list mission segments and provide checkboxes
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Mission Segments"])
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        segments_v.addWidget(self.tree)

        # Action row: disable/enable segments and clear selected
        action_row = QHBoxLayout()
        self.disable_btn = QPushButton("Disable / Enable")
        self.clear_btn = QPushButton("🗑 Clear Selected")
        self.clear_btn.setStyleSheet(
            "background:#2a1e1e; color:#ffb4b4; border:1px solid #5c2b2b;"
        )

        action_row.addWidget(self.disable_btn)
        action_row.addStretch()
        action_row.addWidget(self.clear_btn)
        segments_v.addLayout(action_row)

        overview_box = QGroupBox("Mission Overview")
        overview_v = QVBoxLayout(overview_box)
        self.profile_widget = MissionProfileWidget()
        self.summary_table = MissionSummaryTable(self)
        overview_v.addWidget(self.profile_widget)
        overview_v.addWidget(self.summary_table)
        overview_v.setStretch(0, 3)
        overview_v.setStretch(1, 2)
        left_v.addWidget(overview_box)


        details_box = QGroupBox("Segment Details")
        details_v = QVBoxLayout(details_box)

        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        details_container = QWidget()
        self.details_layout = QVBoxLayout(details_container)
        self.details_scroll.setWidget(details_container)

        details_v.addWidget(self.details_scroll)
        right_v.addWidget(segments_box, 0)
        right_v.addWidget(details_box, 1)

        left_col.setMinimumWidth(540)
        left_col.setMaximumWidth(780)
        right_col.setMinimumWidth(760)

        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.addWidget(left_col)
        content_splitter.addWidget(right_col)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setHandleWidth(10)
        content_splitter.setSizes([640, 1120])

        main_layout.addWidget(content_splitter)

        self.disable_btn.clicked.connect(self.disable_enable_selected)
        self.clear_btn.clicked.connect(self.clear_selected_segments)
        self.refresh_mission_overview()

    # ====================================================
    # Utilities
    # ====================================================
    def _notify(self, text):
        """Briefly display a message in the segment notice label"""
        self.segment_notice.setText(text)
        self.segment_notice.setVisible(True)
        QTimer.singleShot(2000, lambda: self.segment_notice.setVisible(False))

    def _checked_indices(self):
        """Return a list of indices of checked (selected) segments in the tree."""
        return [
            i for i in range(self.tree.topLevelItemCount())
            if self.tree.topLevelItem(i).checkState(0) == Qt.CheckState.Checked
        ]

    def _selected_indices(self):
        """Return sorted indices for highlighted rows in the segment tree."""
        indices = []
        for item in self.tree.selectedItems():
            idx = self.tree.indexOfTopLevelItem(item)
            if idx >= 0:
                indices.append(idx)
        return sorted(set(indices))

    def _panel_style(self, disabled):
        """Return stylesheet string for a segment panel; visually indicates disabled state."""
        return f"""
            #segmentPanel {{
                background:{'#1a1f2a' if disabled else '#141b29'};
                border:1px solid #2d3a4e;
                border-radius:6px;
                padding:6px;
                margin:4px 0;
                opacity:{'0.45' if disabled else '1.0'};
            }}
        """

    def _wire_segment_summary_signals(self, seg):
        if hasattr(seg, "segment_name_input"):
            seg.segment_name_input.textChanged.connect(self.refresh_mission_overview)
        if hasattr(seg, "nested_dropdown"):
            seg.nested_dropdown.currentIndexChanged.connect(self.refresh_mission_overview)
        if hasattr(seg, "top_dropdown"):
            seg.top_dropdown.currentIndexChanged.connect(self.refresh_mission_overview)
        if hasattr(seg, "config_selector"):
            seg.config_selector.currentIndexChanged.connect(self.refresh_mission_overview)
        if hasattr(seg, "ctrl_points"):
            seg.ctrl_points.textChanged.connect(self.refresh_mission_overview)

    def refresh_mission_overview(self):
        phases = []
        for idx, seg in enumerate(self.segment_widgets):
            if idx in self.disabled_segments:
                continue

            name = ""
            if hasattr(seg, "segment_name_input"):
                name = seg.segment_name_input.text().strip()
            if not name and idx < self.tree.topLevelItemCount():
                name = self.tree.topLevelItem(idx).text(0).strip()
            if not name and hasattr(seg, "nested_dropdown"):
                name = seg.nested_dropdown.currentText().strip()
            ptype = ""
            if hasattr(seg, "top_dropdown"):
                ptype = seg.top_dropdown.currentText().strip().lower()
            sub_text = ""
            if hasattr(seg, "nested_dropdown"):
                sub_text = seg.nested_dropdown.currentText().strip().lower()
            if ptype == "vertical flight" and sub_text:
                ptype = f"vertical {sub_text}"
            elif ptype == "ground" and sub_text:
                ptype = f"ground {sub_text}"
            elif ptype == "single_point":
                ptype = "single_point"
            elif not ptype and sub_text:
                ptype = sub_text
            phases.append((name or f"Segment {idx + 1}", ptype or "other"))

        self.profile_widget.set_phases(phases)
        self.summary_table.update_table()
    # ====================================================
    # Disable / Enable
    # ====================================================

    def disable_enable_selected(self):
        """Toggle enabled/disabled state for all checked segments."""
        indices = self._checked_indices()
        # If user selects nothing, show a warning and return
        if not indices:
            self._notify("⚠ No segments selected")
            return

        messages = []

        for idx in indices:
            seg = self.segment_widgets[idx]
            item = self.tree.topLevelItem(idx)
            name = item.text(0)
            # Each segment has a corresponding panel + separator line; panel is at idx*2
            panel = self.details_layout.itemAt(idx * 2).widget()

            if idx in self.disabled_segments:
                # Enable
                seg.setDisabled(False)
                self.disabled_segments.remove(idx)
                panel.setStyleSheet(self._panel_style(False))
                messages.append(f"✅ '{name}' enabled")
            else:
                # Disable
                seg.setDisabled(True)
                self.disabled_segments.add(idx)
                panel.setStyleSheet(self._panel_style(True))
                messages.append(f"⛔ '{name}' disabled")

        # Show last action message (enable/disable)
        self._notify(messages[-1])
        self.refresh_mission_overview()

    # ===============================
    # Clear Selected Segments
    # ===============================
    def clear_selected_segments(self):
        """Remove highlighted segments from UI and internal lists."""
        # Remove from highest index to avoid reindex issues
        indices = sorted(self._selected_indices(), reverse=True)
        if not indices:
            self._notify("⚠ No segments selected")
            return

        messages = []

        for idx in indices:
            item = self.tree.topLevelItem(idx)
            name = item.text(0)

            # Remove from tree and internal segment list
            self.tree.takeTopLevelItem(idx)
            self.segment_widgets.pop(idx)
            self.disabled_segments = {
                i - 1 if i > idx else i
                for i in self.disabled_segments
                if i != idx
            }

            # Each segment consists of a panel and a horizontal line => remove both
            for _ in range(2):
                it = self.details_layout.takeAt(idx * 2)
                if it and it.widget():
                    it.widget().deleteLater()

            messages.append(f"🗑 '{name}' cleared")

        # Show last cleared segment
        self._notify(messages[-1])
        self.refresh_mission_overview()

    # ====================================================
    # Add Segment
    # ====================================================
    def add_segment(self):
        """Create a new MissionSegmentWidget and add it to the UI and internal state."""
        seg = MissionSegmentWidget()
        # Default to a simple cruise segment for quick GUI validation
        try:
            seg.top_dropdown.setCurrentIndex(1)  # Cruise
            seg.populate_nested_dropdown(seg.top_dropdown.currentIndex())
            seg.nested_dropdown.setCurrentText("Constant Speed/Constant Altitude")
            seg.segment_name_input.setText("cruise")
            if hasattr(seg, "_apply_defaults"):
                seg._apply_defaults()
        except Exception:
            pass
        self.segment_widgets.append(seg)
        self._wire_segment_summary_signals(seg)

        # If user provided a mission name in the input, use it; otherwise fall back
        name = self.mission_name_input.text().strip()
        if not name:
            name = f"Segment {len(self.segment_widgets)}"

        # Wrap the segment in a collapsible panel and add to details layout
        panel = CollapsiblePanel(name.title(), seg)
        panel.setObjectName("segmentPanel")
        panel.setStyleSheet(self._panel_style(False))
        self.details_layout.addWidget(panel)

        # Add a visually separating horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#2b3648; margin:2px 0;")
        self.details_layout.addWidget(line)

        # Add the segment to the list tree (with an unchecked checkbox)
        item = QTreeWidgetItem([name.title()])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked)
        self.tree.addTopLevelItem(item)

        # Clear the input and notify the user
        self.mission_name_input.clear()
        self.refresh_mission_overview()
        self._notify(f"✓ Added '{name.title()}'")

    def save_all_data(self):
        """
        Save mission data and build the RCAIDE mission object.
        This function must not build or modify aircraft configurations.
        """
        import values

        # Reset stored mission data before saving
        values.mission_data = []

        # Save analyses that were already defined by the user

        # Collect data from each enabled mission segment
        for idx, seg in enumerate(self.segment_widgets):
            if idx in self.disabled_segments:
                continue

            seg_data, _ = seg.get_data()
            seg_data["Segment Name"] = self.tree.topLevelItem(idx).text(0)
            values.mission_data.append(seg_data)

        # Create the RCAIDE mission using existing data only
        # Defer mission build until analyses are saved

        # Notify the user that the mission was saved
        self._notify("Mission data saved")
        self.refresh_mission_overview()


    def create_rcaide_mission(self):
        # Create an empty sequential mission container
        rcaide_mission = RCAIDE.Framework.Mission.Sequential_Segments()
        rcaide_mission.tag = self.mission_name_input.text()

        # Add each enabled segment to the mission
        for idx, seg in enumerate(self.segment_widgets):
            if idx in self.disabled_segments:
                continue

            _, rcaide_segment = seg.get_data()

            # Ensure analyses exist before assigning them to a segment
            if not values.rcaide_analyses:
                raise RuntimeError("No RCAIDE analyses available")

            # If the segment has no analyses (should be rare), assign a fallback
            if not getattr(rcaide_segment, "analyses", None):
                rcaide_segment.analyses = next(iter(values.rcaide_analyses.values()))

            # Append the segment to the mission sequence
            rcaide_mission.append_segment(rcaide_segment)

        return rcaide_mission

    # ====================================================
    # Load Mission
    # ====================================================

    def load_from_values(self):
        """Populate the UI from `values.mission_data` previously saved."""
        # Reset UI and internal lists
        self.tree.clear()
        self.segment_widgets = []
        self.disabled_segments.clear()

        # Clear existing widgets in the details layout
        for i in reversed(range(self.details_layout.count())):
            w = self.details_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        # Recreate segments from saved data
        for seg_data in values.mission_data:
            seg = MissionSegmentWidget()
            seg.load_data(seg_data)
            self.segment_widgets.append(seg)
            self._wire_segment_summary_signals(seg)

            name = seg_data.get("Segment Name", "Segment")
            panel = CollapsiblePanel(name.title(), seg)
            panel.setObjectName("segmentPanel")
            panel.setStyleSheet(self._panel_style(False))
            self.details_layout.addWidget(panel)

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color:#2b3648; margin:2px 0;")
            self.details_layout.addWidget(line)

            item = QTreeWidgetItem([name.title()])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked)
            self.tree.addTopLevelItem(item)

        # Defer mission build until analyses are saved to avoid load-time errors.
        self.refresh_mission_overview()


def get_widget() -> QWidget:
    """Factory helper used to create a MissionWidget instance for the tab system."""
    return MissionWidget()
