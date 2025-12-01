# ============================================================
#  mission.py — Collapsible Segments + Altitude Diagram + Summary Table
# ============================================================

from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QComboBox, QFormLayout, QGridLayout
)

from tabs.mission.widgets import MissionSegmentWidget
from tabs.analysis.analysis import AnalysisWidget
from tabs import TabWidget
import values
import RCAIDE


# ============================================================
#  Collapsible Panel wrapper
# ============================================================
class CollapsiblePanel(QWidget):
    def __init__(self, title: str, content_widget: QWidget):
        super().__init__()
        self.is_open = True
        self.content = content_widget

        self.toggle_btn = QPushButton(f"▼  {title}")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.clicked.connect(self.toggle)
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.content)

    def toggle(self):
        self.is_open = not self.is_open
        self.content.setVisible(self.is_open)
        self.toggle_btn.setText(f"{'▼' if self.is_open else '►'}  {self.toggle_btn.text()[2:]}")


# ============================================================
#  Mission Profile (original line diagram)
# ============================================================
class MissionProfileWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(140)
        self.setMaximumHeight(180)
        self.phases: list[str] = []
        self._progress = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_animation)
        self._timer.start(40)
        self.setAutoFillBackground(False)
        

    def set_phases(self, names: list[str]) -> None:
        self.phases = [n.title() for n in names] if names else []
        self.update()

    def _advance_animation(self):
        if not self.phases or len(self.phases) < 2:
            return
        self._progress += 0.005
        if self._progress > 1.0:
            self._progress = 0.0
        self.update()

    @staticmethod
    def _phase_type(name: str) -> str:
        n = name.lower()
        if "takeoff" in n or "taxi" in n:
            return "takeoff"
        if "climb" in n:
            return "climb"
        if "cruise" in n:
            return "cruise"
        if "descent" in n or "des" in n:
            return "descent"
        if "landing" in n or "land" in n:
            return "landing"
        return "other"

    def _phase_color(self, ptype: str) -> QColor:
        colors = {
            "takeoff": "#4caf50",
            "climb": "#81c784",
            "cruise": "#64b5f6",
            "descent": "#ffb74d",
            "landing": "#e57373",
        }
        return QColor(colors.get(ptype, "#b0bec5"))

    def _phase_icon(self, ptype: str) -> str:
        icons = {
            "takeoff": "🛫",
            "climb": "↗",
            "cruise": "☁",
            "descent": "↘",
            "landing": "🛬",
        }
        return icons.get(ptype, "•")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect().adjusted(18, 16, -18, -28)
        painter.fillRect(self.rect(), QColor("#050a12"))

        # Light gridlines
        painter.setPen(QPen(QColor("#1f2933"), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = rect.top() + i * rect.height() / 4
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))

        if not self.phases:
            painter.setPen(QColor("#8c9aa8"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "Mission profile will appear here once you add segments.")
            return

        n = len(self.phases)
        alt = []
        cur = 0.15
        for name in self.phases:
            ptype = self._phase_type(name)
            if ptype in ("takeoff", "climb"):
                cur += 0.18
            elif ptype == "cruise":
                cur += 0.0
            elif ptype in ("descent", "landing"):
                cur -= 0.18
            else:
                cur += 0.05
            cur = max(0.08, min(0.85, cur))
            alt.append(cur)
        alt.insert(0, 0.08)

        dx = rect.width() / n
        xs = [rect.left() + i * dx for i in range(n + 1)]

        painter.setFont(QFont("Segoe UI", 9))
        for i, name in enumerate(self.phases):
            ptype = self._phase_type(name)
            color = self._phase_color(ptype)
            x1, x2 = xs[i], xs[i + 1]
            y1 = rect.bottom() - alt[i] * rect.height()
            y2 = rect.bottom() - alt[i + 1] * rect.height()

            seg_path = QPainterPath()
            seg_path.moveTo(x1, y1)
            seg_path.lineTo(x2, y2)
            painter.setPen(QPen(color, 2.0))
            painter.drawPath(seg_path)

            cx = 0.5 * (x1 + x2)
            label_y = min(y1, y2) - 16
            label_y = max(label_y, rect.top() + 4)
            icon = self._phase_icon(ptype)
            label = f"{icon}  {name}"
            painter.setPen(QColor("#e8f2ff"))
            painter.drawText(int(cx - 50), int(label_y), 100, 18,
                             Qt.AlignmentFlag.AlignCenter, label)

        painter.setPen(QPen(QColor("#3f5670"), 1.2))
        painter.drawLine(int(rect.left()), int(rect.bottom()),
                         int(rect.right()), int(rect.bottom()))

        # ✈ Animation
        total_segments = n
        t = self._progress * total_segments
        idx = int(t)
        frac = t - idx
        if idx >= total_segments:
            idx = total_segments - 1
            frac = 1.0
        x1, x2 = xs[idx], xs[idx + 1]
        y1 = rect.bottom() - alt[idx] * rect.height()
        y2 = rect.bottom() - alt[idx + 1] * rect.height()
        mx = x1 + (x2 - x1) * frac
        my = y1 + (y2 - y1) * frac
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(mx, my), 4, 4)
        painter.setPen(QPen(QColor("#64b5f6"), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(mx, my), 7, 7)

# ============================================================
#  Mission Summary Table (Stable + Compatible)
# ============================================================
class MissionSummaryTable(QTableWidget):
    def __init__(self, mission_widget):
        super().__init__(0, 8)
        self.mission_widget = mission_widget

        self.setMinimumHeight(240)
        self.setMaximumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setHorizontalHeaderLabels([
            "Name", "Type", "Altitude", "Velocity",
            "Throttle", "Ctrl Pts", "Unknowns", "Residuals"
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.setStyleSheet("""
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
                padding:5px;
            }
            QTableWidget::item:selected {
                background-color:#1b2a44;
            }
        """)

        self._show_placeholder()
        self.cellClicked.connect(self._row_clicked)

    def _show_placeholder(self):
        self.clearContents()
        self.setRowCount(1)
        placeholder = QTableWidgetItem("No segments added yet.")
        placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(0, 0, placeholder)
        self.setSpan(0, 0, 1, 8)

    def update_table(self):
        segs = self.mission_widget.segment_widgets
        if not segs:
            self._show_placeholder()
            return

        self.clearContents()
        self.setRowCount(len(segs))

        for row, seg in enumerate(segs):
            try:
                data, _ = seg.get_data()
            except Exception:
                data = {}

            name = data.get("Segment Name", f"Segment {row + 1}")
            s_type = data.get("Segment Type", "Custom")
            alt = data.get("Altitude", 0.0)
            vel = data.get("Velocity End", 0.0)
            throttle = data.get("Throttle", 1.0)
            ctrl_pts = seg.ctrl_points.text() if hasattr(seg, "ctrl_points") else "2"
            unknowns = len(data.get("Degrees of Freedom", []))
            residuals = len(data.get("Residuals", []))

            vals = [name, s_type, alt, vel, throttle,
                    ctrl_pts, unknowns, residuals]

            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.setItem(row, col, item)

        self.resizeColumnsToContents()
        self.setFixedHeight(240)

    def _row_clicked(self, row, col):
        panel_index = row * 2
        layout = self.mission_widget.details_layout
        if panel_index < layout.count():
            widget = layout.itemAt(panel_index).widget()
            if hasattr(widget, "toggle") and not widget.is_open:
                widget.toggle()
            self.mission_widget.details_scroll.ensureWidgetVisible(widget)


# ============================================================
#  Mission Widget (Main)
# ============================================================
class MissionWidget(TabWidget):
    def __init__(self):
        super().__init__()
        root = QSplitter(Qt.Orientation.Horizontal)
        root.setHandleWidth(2)
        root.setChildrenCollapsible(False)

        # LEFT COLUMN
        left_col = QWidget()
        left_v = QVBoxLayout(left_col)
        left_v.setContentsMargins(10, 10, 10, 10)

        analyses_box = QGroupBox("Mission Analyses")
        analyses_v = QVBoxLayout(analyses_box)
        analyses_v.addWidget(AnalysisWidget())
        left_v.addWidget(analyses_box, 3)

        segs_box = QGroupBox("Mission Segments")
        segs_v = QVBoxLayout(segs_box)
        name_row = QHBoxLayout()
        name_label = QLabel("Mission Name:")
        name_label.setStyleSheet("color:#dbe7ff;")
        self.mission_name_input = QLineEdit()
        self.mission_name_input.setPlaceholderText("Enter mission name...")
        name_row.addWidget(name_label)
        name_row.addWidget(self.mission_name_input)
        segs_v.addLayout(name_row)

        btn_row = QHBoxLayout()
        self.add_segment_btn = QPushButton("➕ Add Segment")
        self.save_btn = QPushButton("💾 Save All Data")
        for b in (self.add_segment_btn, self.save_btn):
            b.setStyleSheet("background-color:#141b29; color:#e5f0ff;")
        self.add_segment_btn.clicked.connect(self.add_segment)
        self.save_btn.clicked.connect(self.save_all_data)
        btn_row.addWidget(self.add_segment_btn)
        btn_row.addWidget(self.save_btn)
        segs_v.addLayout(btn_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Mission Segments"])
        segs_v.addWidget(self.tree)
        left_v.addWidget(segs_box, 2)

        # RIGHT COLUMN
        right_col = QWidget()
        right_v = QVBoxLayout(right_col)
        right_v.setContentsMargins(10, 10, 10, 10)

        # Mission Profile
        profile_box = QGroupBox("Mission Profile")
        profile_v = QVBoxLayout(profile_box)
        self.profile_widget = MissionProfileWidget()
        profile_v.addWidget(self.profile_widget)
        right_v.addWidget(profile_box)

        # Mission Summary Table
        self.summary_table = MissionSummaryTable(self)
        right_v.addWidget(self.summary_table)

        # Segment Details
        details_box = QGroupBox("Segment Details")
        details_v = QVBoxLayout(details_box)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        details_container = QWidget()
        self.details_layout = QVBoxLayout(details_container)
        self.details_scroll.setWidget(details_container)
        details_v.addWidget(self.details_scroll)
        right_v.addWidget(details_box, 1)

        root.addWidget(left_col)
        root.addWidget(right_col)
        layout = QVBoxLayout(self)
        layout.addWidget(root)
        self.segment_widgets = []

    # ============================================================
    #  Segment handlers (CLEAN + COMPACT + GREY CONTAINER)
    # ============================================================
    # Segment handlers
    def add_segment(self):
        seg = MissionSegmentWidget()
        seg_layout = getattr(seg, "main_layout", None) or getattr(seg, "layout", lambda: None)()

        # Force compact grid-like alignment (no vertical gaps)
        if isinstance(seg_layout, (QFormLayout, QGridLayout)):
            seg_layout.setSpacing(2)
            seg_layout.setContentsMargins(4, 0, 4, 0)
        else:
            try:
                seg_layout.setSpacing(2)
                seg_layout.setContentsMargins(4, 0, 4, 0)
            except Exception:
                pass

        # Compact input widgets
        for widget in seg.findChildren((QLabel, QLineEdit, QComboBox)):
            if isinstance(widget, QLabel):
                widget.setStyleSheet("QLabel { color:#dbe7ff; margin:0; padding:0; }")
            elif isinstance(widget, QLineEdit):
                widget.setFixedHeight(22)
                widget.setStyleSheet("""
                    QLineEdit {
                        background-color:#2b3038;
                        border:1px solid #3a475a;
                        border-radius:3px;
                        padding:1px 3px;
                        color:#e5f0ff;
                        font-size:11px;
                        margin:0;
                    }
                """)
            elif isinstance(widget, QComboBox):
                widget.setFixedHeight(22)
                widget.setStyleSheet("""
                    QComboBox {
                        background-color:#2b3038;
                        border:1px solid #3a475a;
                        border-radius:3px;
                        padding:1px 3px;
                        color:#e5f0ff;
                        font-size:11px;
                        margin:0;
                    }
                    QComboBox::drop-down { width:14px; border:none; }
                """)

        # Add compact control points row
        ctrl_row = QHBoxLayout()
        ctrl_row.setContentsMargins(0, 0, 0, 0)
        ctrl_row.setSpacing(4)

        seg.ctrl_label = QLabel("Number of Control Points:")
        seg.ctrl_label.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")

        seg.ctrl_points = QLineEdit("2")
        seg.ctrl_points.setFixedWidth(70)
        seg.ctrl_points.setFixedHeight(22)
        seg.ctrl_points.setAlignment(Qt.AlignmentFlag.AlignCenter)
        seg.ctrl_points.setStyleSheet("""
            QLineEdit {
                background-color:#2b3038;
                border:1px solid #3a475a;
                border-radius:3px;
                padding:1px 3px;
                color:#e5f0ff;
                font-size:11px;
                margin:0;
            }
        """)

        ctrl_row.addWidget(seg.ctrl_label)
        ctrl_row.addWidget(seg.ctrl_points)
        ctrl_row.addStretch(1)

        if seg_layout:
            seg_layout.insertLayout(0, ctrl_row)

        # Build collapsible container
        title = seg.get_default_name().title() if hasattr(seg, "get_default_name") else f"Segment {len(self.segment_widgets)+1}"
        panel = CollapsiblePanel(title, seg)
        panel.setMaximumWidth(900)      # << reduce this number to shrink more
        panel.setMinimumWidth(900) 
        panel.setStyleSheet("""
            QWidget {
                background-color:#1c2129;
                border-radius:4px;
                margin:0;
                padding:2px;
            }
        """)

        self.segment_widgets.append(seg)
        self.details_layout.addWidget(panel)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#2b3648; margin:2px 0;")
        self.details_layout.addWidget(line)

        self.tree.addTopLevelItem(QTreeWidgetItem([title]))
        self._update_profile()
        self.summary_table.update_table()

    def _update_profile(self):
        names = []
        for seg in self.segment_widgets:
            try:
                data, _ = seg.get_data()
                names.append(data.get("Segment Name", "Segment"))
            except Exception:
                names.append("Segment")
        self.profile_widget.set_phases(names)
        self.summary_table.update_table()

    def save_all_data(self):
        self.tree.clear()
        values.mission_data = []
        values.rcaide_mission = RCAIDE.Framework.Mission.Sequential_Segments()
        values.rcaide_mission.tag = self.mission_name_input.text()

        for idx, seg in enumerate(self.segment_widgets, start=1):
            data, rseg = seg.get_data()
            try:
                cp = int(seg.ctrl_points.text())
            except Exception:
                cp = 2
            rseg.control_points = cp
            data["Control Points"] = cp
            values.mission_data.append(data)
            values.rcaide_mission.append_segment(rseg)
            seg_name = data.get("Segment Name", f"Segment {idx}")
            self.tree.addTopLevelItem(QTreeWidgetItem([seg_name.title()]))

        self._update_profile()
        self.summary_table.update_table()

    def load_from_values(self):
        self.tree.clear()
        for i in reversed(range(self.details_layout.count())):
            w = self.details_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        self.segment_widgets = []
        values.rcaide_mission = RCAIDE.Framework.Mission.Sequential_Segments()
        values.rcaide_mission.tag = self.mission_name_input.text()

        for seg_data in values.mission_data:
            seg = MissionSegmentWidget()
            seg.load_data(seg_data)
            seg_layout = getattr(seg, "main_layout", None) or getattr(seg, "layout", lambda: None)()

            if isinstance(seg_layout, (QFormLayout, QGridLayout)):
                seg_layout.setSpacing(2)
                seg_layout.setContentsMargins(4, 0, 4, 0)
            else:
                try:
                    seg_layout.setSpacing(2)
                    seg_layout.setContentsMargins(4, 0, 4, 0)
                except Exception:
                    pass

            ctrl_row = QHBoxLayout()
            ctrl_row.setContentsMargins(0, 0, 0, 0)
            ctrl_row.setSpacing(4)

            seg.ctrl_label = QLabel("Number of Control Points:")
            seg.ctrl_label.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")

            seg.ctrl_points = QLineEdit(str(seg_data.get("Control Points", 2)))
            seg.ctrl_points.setFixedWidth(70)
            seg.ctrl_points.setFixedHeight(22)
            seg.ctrl_points.setAlignment(Qt.AlignmentFlag.AlignCenter)
            seg.ctrl_points.setStyleSheet("""
                QLineEdit {
                    background-color:#2b3038;
                    border:1px solid #3a475a;
                    border-radius:3px;
                    padding:1px 3px;
                    color:#e5f0ff;
                    font-size:11px;
                    margin:0;
                }
            """)

            ctrl_row.addWidget(seg.ctrl_label)
            ctrl_row.addWidget(seg.ctrl_points)
            ctrl_row.addStretch(1)
            seg_layout.insertLayout(0, ctrl_row)

            for widget in seg.findChildren((QLabel, QLineEdit, QComboBox)):
                if isinstance(widget, QLabel):
                    widget.setStyleSheet("QLabel { color:#dbe7ff; margin:0; padding:0; }")
                elif isinstance(widget, QLineEdit):
                    widget.setFixedHeight(22)
                    widget.setStyleSheet("""
                        QLineEdit {
                            background-color:#2b3038;
                            border:1px solid #3a475a;
                            border-radius:3px;
                            padding:1px 3px;
                            color:#e5f0ff;
                            font-size:11px;
                            margin:0;
                        }
                    """)
                elif isinstance(widget, QComboBox):
                    widget.setFixedHeight(22)
                    widget.setStyleSheet("""
                        QComboBox {
                            background-color:#2b3038;
                            border:1px solid #3a475a;
                            border-radius:3px;
                            padding:1px 3px;
                            color:#e5f0ff;
                            font-size:11px;
                            margin:0;
                        }
                        QComboBox::drop-down { width:14px; border:none; }
                    """)

            self.segment_widgets.append(seg)
            panel = CollapsiblePanel(seg_data.get("Segment Name", "Segment").title(), seg)
            panel.setStyleSheet("""
                QWidget {
                    background-color:#1c2129;
                    border-radius:4px;
                    margin:0;
                    padding:2px;
                }
            """)
            self.details_layout.addWidget(panel)

            rseg = seg.create_rcaide_segment()
            rseg.control_points = seg_data.get("Control Points", 2)
            values.rcaide_mission.append_segment(rseg)
            self.tree.addTopLevelItem(QTreeWidgetItem([seg_data.get("Segment Name", "Segment").title()]))

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color:#2b3648; margin:2px 0;")
            self.details_layout.addWidget(line)

        self._update_profile()
        self.summary_table.update_table()


def get_widget() -> QWidget:
    return MissionWidget()
