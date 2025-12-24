from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QComboBox, QFormLayout, QGridLayout, QRadioButton
)

from tabs.mission.widgets import MissionSegmentWidget
from tabs.mission.widgets import MissionAnalysisWidget as MissionAnalysisWidget
from tabs import TabWidget
import values
import RCAIDE

# ============================================================
#  Collapsible Panel wrapper
# ============================================================
class CollapsiblePanel(QWidget):
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
        # Toggle open/closed state
        self.is_open = not self.is_open

        # Show or hide the content widget
        self.content.setVisible(self.is_open)

        # Update arrow icon in the header text
        self.toggle_btn.setText(
            f"{'▼' if self.is_open else '►'}  {self.toggle_btn.text()[2:]}"
        )

# ============================================================
#  Mission Profile (line Diagram)
# ============================================================
class MissionProfileWidget(QWidget):
    def __init__(self, parent=None):
        # Initialize the base QWidget
        super().__init__(parent)

        # Set minimum and maximum height for consistent layout
        self.setMinimumHeight(140)
        self.setMaximumHeight(180)

        # List of mission phase names (e.g., takeoff, climb, cruise)
        self.phases: list[str] = []

        # Normalized animation progress value (0.0 → 1.0)
        self._progress = 0.0

        # Timer to drive the animated progress indicator
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_animation)
        self._timer.start(40)

        # Disable automatic background fill (custom painting is used)
        self.setAutoFillBackground(False)

    def set_phases(self, names: list[str]) -> None:
        # Store phase names in title case for display
        self.phases = [n.title() for n in names] if names else []

        # Trigger a repaint when phases change
        self.update()

    def _advance_animation(self):
        # Skip animation if there are not enough phases
        if not self.phases or len(self.phases) < 2:
            return

        # Advance animation progress
        self._progress += 0.005

        # Loop animation once it reaches the end
        if self._progress > 1.0:
            self._progress = 0.0
    
        # Request a repaint for the next frame
        self.update()

    @staticmethod
    def _phase_type(name: str) -> str:
        # Determine phase type based on keywords in the phase name
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

        # Default fallback for unrecognized phase names
        return "other"

    def _phase_color(self, ptype: str) -> QColor:
        # Color mapping for each mission phase type
        colors = {
            "takeoff": "#4caf50",
            "climb": "#81c784",
            "cruise": "#64b5f6",
            "descent": "#ffb74d",
            "landing": "#e57373",
        }
        # Return mapped color or default color if type is unknown
        return QColor(colors.get(ptype, "#b0bec5"))

    def _phase_icon(self, ptype: str) -> str:
        # Icon mapping for each mission phase type
        icons = {
            "takeoff": "🛫",
            "climb": "↗",
            "cruise": "☁",
            "descent": "↘",
            "landing": "🛬",
        }

        # Return icon for phase type, or a default bullet
        return icons.get(ptype, "•")

    def paintEvent(self, event):
        # Create painter for custom drawing
        painter = QPainter(self)

        # Enable smoother rendering
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Define drawing area with margins
        rect = self.rect().adjusted(18, 16, -18, -28)

        # Fill widget background
        painter.fillRect(self.rect(), QColor("#050a12"))

        # Draw light horizontal gridlines
        painter.setPen(QPen(QColor("#1f2933"), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = rect.top() + i * rect.height() / 4
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))

        # If no mission phases exist, show placeholder text
        if not self.phases:
            painter.setPen(QColor("#8c9aa8"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Mission profile will appear here once you add segments."
            )
            return

        # Number of mission phases
        n = len(self.phases)

        # Build normalized altitude profile
        alt = []
        cur = 0.15
        for name in self.phases:
            ptype = self._phase_type(name)

            # Adjust altitude based on phase type
            if ptype in ("takeoff", "climb"):
                cur += 0.18
            elif ptype == "cruise":
                cur += 0.0
            elif ptype in ("descent", "landing"):
                cur -= 0.18
            else:
                cur += 0.05

            # Clamp altitude to visible bounds
            cur = max(0.08, min(0.85, cur))
            alt.append(cur)

        # Insert starting altitude
        alt.insert(0, 0.08)

        # Compute x positions for each segment boundary
        dx = rect.width() / n
        xs = [rect.left() + i * dx for i in range(n + 1)]

        # Set font for phase labels
        painter.setFont(QFont("Segoe UI", 9))

        # Draw each mission segment
        for i, name in enumerate(self.phases):
            ptype = self._phase_type(name)
            color = self._phase_color(ptype)

            # Segment endpoints
            x1, x2 = xs[i], xs[i + 1]
            y1 = rect.bottom() - alt[i] * rect.height()
            y2 = rect.bottom() - alt[i + 1] * rect.height()

            # Draw segment line
            seg_path = QPainterPath()
            seg_path.moveTo(x1, y1)
            seg_path.lineTo(x2, y2)
            painter.setPen(QPen(color, 2.0))
            painter.drawPath(seg_path)

            # Compute label position
            cx = 0.5 * (x1 + x2)
            label_y = min(y1, y2) - 16
            label_y = max(label_y, rect.top() + 4)

            # Build label text with icon
            icon = self._phase_icon(ptype)
            label = f"{icon}  {name}"

            # Draw phase label
            painter.setPen(QColor("#e8f2ff"))
            painter.drawText(
                int(cx - 50),
                int(label_y),
                100,
                18,
                Qt.AlignmentFlag.AlignCenter,
                label
            )
        # Draw baseline (ground reference)
        painter.setPen(QPen(QColor("#3f5670"), 1.2))
        painter.drawLine(
            int(rect.left()),
            int(rect.bottom()),
            int(rect.right()),
            int(rect.bottom())
        )
        # --- Draw animated progress marker ---
        # Convert progress to segment index and interpolation fraction
        total_segments = n
        t = self._progress * total_segments
        idx = int(t)
        frac = t - idx

        # Clamp animation at the final segment
        if idx >= total_segments:
            idx = total_segments - 1
            frac = 1.0

        # Interpolate position along current segment
        x1, x2 = xs[idx], xs[idx + 1]
        y1 = rect.bottom() - alt[idx] * rect.height()
        y2 = rect.bottom() - alt[idx + 1] * rect.height()
        mx = x1 + (x2 - x1) * frac
        my = y1 + (y2 - y1) * frac

        # Draw inner marker dot
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(mx, my), 4, 4)

        # Draw outer marker ring
        painter.setPen(QPen(QColor("#64b5f6"), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(mx, my), 7, 7)

# =======================================
#  Mission Summary Table
# =======================================
class MissionSummaryTable(QTableWidget):
    def __init__(self, mission_widget):
        # Initialize table with 0 rows and 5 columns
        super().__init__(0, 5)

        # Reference to the parent mission widget
        self.mission_widget = mission_widget

        # Set a minimum width for each column
        self.horizontalHeader().setMinimumSectionSize(80)

        # Allow table to expand horizontally but keep fixed height
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        # Define column headers
        self.setHorizontalHeaderLabels([
            "Segment Name",
            "Subsegment Type",
            "Ctrl Pts",
            "Unknowns",
            "Residuals"
        ])
        # Stretch columns to fill available width
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        # Hide vertical row numbers
        self.verticalHeader().setVisible(False)

        # Enable full-row selection behavior
        self.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        # Disable direct cell editing
        self.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        # Apply dark theme styling for table and headers
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
        # Handle clicks on table rows
        self.cellClicked.connect(self._row_clicked)

    # ========================================================
    # Update summary table (fixed subsegment type)
    # ========================================================
    def update_table(self):
        # Retrieve all mission segment widgets
        segs = self.mission_widget.segment_widgets

        # If no segments exist, show placeholder message
        if not segs:
            self.clearContents()
            self.setRowCount(1)

            # Single centered message spanning all columns
            item = QTableWidgetItem("No segments added yet.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(0, 0, item)
            self.setSpan(0, 0, 1, 5)
            return

        # Temporary storage for row data
        rows = []

        # Collect data from each mission segment
        for seg in segs:
            data, _ = seg.get_data()

            # Segment display name
            name = data.get("Segment Name", "")

            # Subsegment type from the actual dropdown (authoritative source)
            subsegment = seg.nested_dropdown.currentText()

            # Control points (default to "2" if widget does not exist)
            cp = seg.ctrl_points.text() if hasattr(seg, "ctrl_points") else "2"

            # Count unknowns and residuals
            unknowns = len(data.get("Degrees of Freedom", []))
            residuals = len(data.get("Residuals", []))

            # Store lowercase name for sorting, plus display values
            rows.append((name.lower(), name, subsegment, cp, unknowns, residuals))

        # Sort rows so that "takeoff" appears first
        rows.sort(key=lambda r: (r[0] != "takeoff"))

        # Apply rows to the table
        self.clearContents()
        self.setRowCount(len(rows))

        # Populate table cells
        for r, (_, name, subsegment, cp, un, re) in enumerate(rows):
            vals = [name, subsegment, cp, un, re]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(r, c, item)
        # --- Auto-adjust table height to fit all rows ---
        total_height = (
            self.horizontalHeader().height() +
            (self.rowHeight(0) * len(rows)) +
            4
        )
        self.setFixedHeight(total_height)

    # ============================================================
    # Clicking a row scrolls to its details panel
    # ============================================================
    def _row_clicked(self, row, col):
        # Get the segment name from the first column of the clicked row
        seg_name = self.item(row, 0).text().lower()

        # Find the matching segment widget index
        target_index = None
        for i, seg in enumerate(self.mission_widget.segment_widgets):
            data, _ = seg.get_data()
            if data.get("Segment Name", "").lower() == seg_name:
                target_index = i
                break

        # Exit if no matching segment was found
        if target_index is None:
            return

        # Each segment corresponds to a collapsible panel + spacer,
        # so the panel index is doubled
        panel_index = target_index * 2

        # Reference the layout that holds the segment detail panels
        layout = self.mission_widget.details_layout

        # Ensure the target panel exists in the layout
        if panel_index < layout.count():
            widget = layout.itemAt(panel_index).widget()

            # Expand the panel if it is currently collapsed
            if hasattr(widget, "toggle") and not widget.is_open:
                widget.toggle()

            # Scroll the details area so the panel becomes visible
            self.mission_widget.details_scroll.ensureWidgetVisible(widget)

# ============================================================
#  Mission Widget (Main)
# ============================================================
class MissionWidget(TabWidget):
    def __init__(self, shared_analysis_widget=None):
        super().__init__()

        # Use shared analysis widget if provided, otherwise create a new one
        if shared_analysis_widget is not None:
            self.analysis_widget = shared_analysis_widget
        else:
            self.analysis_widget = MissionAnalysisWidget()

        # Root horizontal splitter separating left and right columns
        root = QSplitter(Qt.Orientation.Horizontal)
        root.setHandleWidth(2)
        root.setChildrenCollapsible(False)

        # --- Left column ---
        left_col = QWidget()
        left_v = QVBoxLayout(left_col)
        left_v.setContentsMargins(10, 10, 10, 10)

        # Mission analyses section
        analyses_box = QGroupBox("Mission Analyses")
        analyses_v = QVBoxLayout(analyses_box)
        analyses_v.addWidget(MissionAnalysisWidget())
        left_v.addWidget(analyses_box, 3)

        # Mission segments section
        segs_box = QGroupBox("Mission Segments")
        segs_v = QVBoxLayout(segs_box)

        # Mission name input row
        name_row = QHBoxLayout()
        name_label = QLabel("Mission Name:")
        name_label.setStyleSheet("color:#dbe7ff;")
        self.mission_name_input = QLineEdit()
        self.mission_name_input.setPlaceholderText("Enter mission name...")
        name_row.addWidget(name_label)
        name_row.addWidget(self.mission_name_input)
        segs_v.addLayout(name_row)

        # Action buttons row
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

        # Tree view listing mission segments
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Mission Segments"])
        segs_v.addWidget(self.tree)
        left_v.addWidget(segs_box, 2)

        # --- Right column ---
        right_col = QWidget()
        right_v = QVBoxLayout(right_col)
        right_v.setContentsMargins(10, 10, 10, 10)

        # Mission profile visualization
        profile_box = QGroupBox("Mission Profile")
        profile_v = QVBoxLayout(profile_box)
        self.profile_widget = MissionProfileWidget()
        profile_v.addWidget(self.profile_widget)
        right_v.addWidget(profile_box)

        # Mission summary table
        self.summary_table = MissionSummaryTable(self)
        right_v.addWidget(self.summary_table)

        # Segment detail panels (scrollable)
        details_box = QGroupBox("Segment Handlers")
        details_v = QVBoxLayout(details_box)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        details_container = QWidget()
        self.details_layout = QVBoxLayout(details_container)
        self.details_scroll.setWidget(details_container)
        details_v.addWidget(self.details_scroll)
        right_v.addWidget(details_box, 1)

        # Add left and right columns to the root splitter
        root.addWidget(left_col)
        root.addWidget(right_col)

        # --- Main Layout ---
        layout = QVBoxLayout(self)
        layout.addWidget(root)

        # Auto-center splitter sizes after initial layout
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: root.setSizes([1000, 1000]))

        # Storage for active mission segment widgets
        self.segment_widgets = []
       
    # ============================================================
    #  Segment Handlers
    # ============================================================
    def add_segment(self):
        # Create a new mission segment widget
        seg = MissionSegmentWidget()

        # Attempt to retrieve the segment’s main layout (supports multiple layout names)
        seg_layout = getattr(seg, "main_layout", None) or getattr(seg, "layout", lambda: None)()

        # --- Compact UI ---
        # Reduce spacing and margins to keep the segment panel tight
        try:
            seg_layout.setSpacing(2)
            seg_layout.setContentsMargins(4, 0, 4, 0)
        except:
            # If layout access fails, continue without breaking
            pass

        # --- Style fixes ---
        # Apply consistent styling to labels, text inputs, and dropdowns
        for widget in seg.findChildren((QLabel, QLineEdit, QComboBox)):

            # Style labels
            if isinstance(widget, QLabel):
                widget.setStyleSheet(
                    "QLabel { color:#dbe7ff; margin:0; padding:0; }"
                )
            # Style text input fields
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
                    }
                """)
            # Style combo box dropdowns
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
                    }
                    QComboBox::drop-down { width:14px; border:none; }
                """)
        
        # ============================================================
        #  Panel Wrapper
        # ============================================================
        # Determine panel title from segment default name or fallback numbering
        title = seg.get_default_name().title() if hasattr(
            seg, "get_default_name"
        ) else f"Segment {len(self.segment_widgets)+1}"

        # Wrap the segment widget inside a collapsible panel
        panel = CollapsiblePanel(title, seg)
        panel.setObjectName("segmentPanel")

        # Force consistent panel width for alignment
        panel.setMaximumWidth(900)
        panel.setMinimumWidth(900)

        # Apply visual styling to the panel container
        panel.setStyleSheet("""
            #segmentPanel {
                background:#141b29;
                border:1px solid #2d3a4e;
                border-radius:6px;
                padding:6px;
                margin:4px 0;
            }
        """)
        # Track the segment widget internally
        self.segment_widgets.append(seg)

        # Add the panel to the scrollable details layout
        self.details_layout.addWidget(panel)

        # --- Divider between panels ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#2b3648; margin:2px 0;")
        self.details_layout.addWidget(line)

        # --- Tree view update ---
        # Add segment entry to the mission segment tree
        self.tree.addTopLevelItem(QTreeWidgetItem([title]))

        # Refresh mission profile visualization
        self._update_profile()

        # Refresh mission summary table
        self.summary_table.update_table()

    # ============================================================
    # Profile Update
    # ============================================================
    def _update_profile(self):
        # Collect segment names for the mission profile
        names = []

        # Loop through all segment widgets
        for seg in self.segment_widgets:
            try:
                # Retrieve segment data and extract the segment name
                data, _ = seg.get_data()
                names.append(data.get("Segment Name", "Segment"))
            except:
                # Fallback if data retrieval fails
                names.append("Segment")

        # Update the mission profile diagram with new phase names
        self.profile_widget.set_phases(names)

        # Refresh the mission summary table to stay in sync
        self.summary_table.update_table()

    # ============================================================
    # Save Mission Data
    # ============================================================
    def save_all_data(self):
        # Clear existing tree entries
        self.tree.clear()

        # Reset stored mission data
        values.mission_data = []

        # Create a new RCAIDE sequential mission container
        values.rcaide_mission = RCAIDE.Framework.Mission.Sequential_Segments()
        values.rcaide_mission.tag = self.mission_name_input.text()

        # Loop through all segment widgets and extract their data
        for idx, seg in enumerate(self.segment_widgets, start=1):
            data, rseg = seg.get_data()

            # --- Control points ---
            # Parse control points from UI, fallback to 2 if invalid
            try:
                cp = int(seg.ctrl_points.text())
            except:
                cp = 2
            data["Control Points"] = cp
            rseg.control_points = cp

            # --- Solver selection ---
            # Root solver if checked, otherwise optimize
            data["Solver"] = "root" if seg.solver_root.isChecked() else "optimize"

            # Store mission data and append RCAIDE segment
            values.mission_data.append(data)
            values.rcaide_mission.append_segment(rseg)

            # Update tree view with segment name
            seg_name = data.get("Segment Name", f"Segment {idx}")
            self.tree.addTopLevelItem(QTreeWidgetItem([seg_name.title()]))

        # Refresh mission profile and summary table
        self._update_profile()
        self.summary_table.update_table()

    # ============================================================
    # Load Mission Data
    # ============================================================
    def load_from_values(self):
        # Clear tree view
        self.tree.clear()

        # --- Clear existing segment detail UI ---
        for i in reversed(range(self.details_layout.count())):
            w = self.details_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        # Reset internal segment storage
        self.segment_widgets = []

        # Recreate RCAIDE mission container
        values.rcaide_mission = RCAIDE.Framework.Mission.Sequential_Segments()
        values.rcaide_mission.tag = self.mission_name_input.text()

        # Rebuild UI and mission from stored values
        for seg_data in values.mission_data:
            seg = MissionSegmentWidget()
            seg.load_data(seg_data)

            # Attempt to retrieve segment layout
            seg_layout = getattr(seg, "main_layout", None) or getattr(
                seg, "layout", lambda: None
            )()

            # Compact layout styling
            try:
                seg_layout.setSpacing(2)
                seg_layout.setContentsMargins(4, 0, 4, 0)
            except:
                pass

            # ============================================================
            # Panel Wrapper (Segment)
            # ============================================================
            # Use saved segment name as panel title
            title = seg_data.get("Segment Name", "Segment").title()

            panel = CollapsiblePanel(title, seg)
            panel.setObjectName("segmentPanel")
            panel.setStyleSheet("""
                #segmentPanel {
                    background:#0d1522;
                    border:1px solid #2d3a4e;
                    border-radius:6px;
                    padding:6px;
                    margin:4px 0;
                }
            """)

            # Track segment and add to UI
            self.segment_widgets.append(seg)
            self.details_layout.addWidget(panel)

            # --- RCAIDE segment reconstruction ---
            rseg = seg.create_rcaide_segment()
            rseg.control_points = seg_data.get("Control Points", 2)
            values.rcaide_mission.append_segment(rseg)

            # Update tree view
            self.tree.addTopLevelItem(QTreeWidgetItem([title]))

            # Divider between panels
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color:#2b3648; margin:2px 0;")
            self.details_layout.addWidget(line)

        # Refresh profile and summary table
        self._update_profile()
        self.summary_table.update_table()

    # ============================================================
    # Remove Duplicate Configuration
    # ============================================================
    def _remove_fake_config_from(self, details_layout, seg):
        try:
            # Iterate through layout items to locate the fake selector
            for i in range(details_layout.count()):
                item = details_layout.itemAt(i)
                w = item.widget()

                if w is seg.config_selector:
                    # Remove label preceding the selector if present
                    if i - 1 >= 0:
                        prev = details_layout.itemAt(i - 1).widget()
                        if isinstance(prev, QLabel) and "Aircraft Configuration" in prev.text():
                            prev.setParent(None)
                            details_layout.removeWidget(prev)

                    # Remove the selector itself
                    w.setParent(None)
                    details_layout.removeWidget(w)
                    break
        except:
            # Fail silently if layout structure differs
            pass

    # ============================================================
    # Add Segment
    # ============================================================
    def add_segment(self):
        # Create a new mission segment widget
        seg = MissionSegmentWidget()

        # Retrieve the segment's main layout
        seg_layout = getattr(seg, "segment_layout", None)
        if seg_layout is None:
            seg_layout = seg.layout()

        # Clean and compact UI layout
        try:
            seg_layout.setSpacing(3)
            seg_layout.setContentsMargins(4, 2, 4, 2)
        except:
            pass

        # Create collapsible panel for the segment
        title = seg.segment_name_input.text() or f"Segment {len(self.segment_widgets)+1}"
        panel = CollapsiblePanel(title, seg)
        panel.setObjectName("segmentPanel")
        panel.setStyleSheet("""
            #segmentPanel {
                background:#141b29;
                border:1px solid #2d3a4e;
                border-radius:6px;
                padding:6px;
                margin:4px 0;
            }
        """)

        # Add panel to UI and track segment
        self.segment_widgets.append(seg)
        self.details_layout.addWidget(panel)

        # Divider between segments
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#2b3648; margin:2px 0;")
        self.details_layout.addWidget(line)

        # Update tree, mission profile, and summary table
        self.tree.addTopLevelItem(QTreeWidgetItem([title]))
        self._update_profile()
        self.summary_table.update_table()

def get_widget(shared_analysis_widget=None) -> QWidget:
    # Factory function for MissionWidget
    return MissionWidget(shared_analysis_widget)