from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QScrollArea, QFrame
)

from tabs.mission.widgets import MissionSegmentWidget
from tabs.mission.widgets import MissionAnalysisWidget
from tabs import TabWidget
import values
import RCAIDE

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

       # Use the provided analysis widget if it exists,
       # otherwise create a new MissionAnalysisWidget
        if isinstance(shared_analysis_widget, MissionAnalysisWidget):
            self.analysis_widget = shared_analysis_widget
        else:
            self.analysis_widget = MissionAnalysisWidget()

        # List of MissionSegmentWidget instances currently in the mission
        self.segment_widgets = []
        # Indices of segments that have been disabled by the user
        self.disabled_segments = set()

        # --- Root splitter ---
        root = QSplitter(Qt.Orientation.Horizontal)
        root.setHandleWidth(2)
        root.setChildrenCollapsible(False)

        # --- Left column: analyses setup (keeps analysis widgets) ---
        left_col = QWidget()
        left_v = QVBoxLayout(left_col)
        left_v.setContentsMargins(10, 10, 10, 10)

        analyses_box = QGroupBox("Analyses Setup (RCAIDE)")
        analyses_v = QVBoxLayout(analyses_box)

        # Add the shared analysis widget instance
        # (Does notcreate a new MissionAnalysisWidget here)
        analyses_v.addWidget(self.analysis_widget)

        left_v.addWidget(analyses_box)

        # --- Right column: mission configuration and segment details ---
        right_col = QWidget()
        right_v = QVBoxLayout(right_col)
        right_v.setContentsMargins(10, 10, 10, 10)

        # =======================================================
        # Mission Setup area (includes segment list and controls)
        # =======================================================
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

        right_v.addWidget(segments_box)

        # ==============================================
        # Segment Details (Area with collapsible panels)
        # ==============================================
        details_box = QGroupBox("Segment Details")
        details_v = QVBoxLayout(details_box)

        # Scroll area that contains a vertical layout of panels
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        details_container = QWidget()
        self.details_layout = QVBoxLayout(details_container)
        self.details_scroll.setWidget(details_container)

        details_v.addWidget(self.details_scroll)
        right_v.addWidget(details_box, 1)

        # Put left and right columns into the splitter
        root.addWidget(left_col)
        root.addWidget(right_col)

        layout = QVBoxLayout(self)
        layout.addWidget(root)

        # Ensure reasonable initial sizes after layout has been set
        QTimer.singleShot(0, lambda: root.setSizes([1000, 1000]))

        # Connect segment control buttons to their handlers
        self.disable_btn.clicked.connect(self.disable_enable_selected)
        self.clear_btn.clicked.connect(self.clear_selected_segments)

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

    # ===============================
    # Clear Selected Segments
    # ===============================
    def clear_selected_segments(self):
        """Remove checked segments from UI and internal lists."""
        # Remove from highest index to avoid reindex issues
        indices = sorted(self._checked_indices(), reverse=True)
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
            self.disabled_segments.discard(idx)

            # Each segment consists of a panel and a horizontal line => remove both
            for _ in range(2):
                it = self.details_layout.takeAt(idx * 2)
                if it and it.widget():
                    it.widget().deleteLater()

            messages.append(f"🗑 '{name}' cleared")

        # Show last cleared segment
        self._notify(messages[-1])

    # ====================================================
    # Add Segment
    # ====================================================
    def add_segment(self):
        """Create a new MissionSegmentWidget and add it to the UI and internal state."""
        seg = MissionSegmentWidget()
        self.segment_widgets.append(seg)

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
        item.setCheckState(0, Qt.CheckState.Unchecked)
        self.tree.addTopLevelItem(item)

        # Clear the input and notify the user
        self.mission_name_input.clear()
        self._notify(f"✓ Added '{name.title()}'")

    # ====================================================
    # Save Mission
    # ====================================================
    def save_all_data(self):
        """Saves all segment data into the global `values` module and build
        an RCAIDE mission object for use by the analysis backend.
        """
        # Reset stored mission data (overwrites previous)
        values.mission_data = []
        self.analysis_widget.save_analyses()

        # Collect data from each enabled segment and append to values
        for idx, seg in enumerate(self.segment_widgets):
            if idx in self.disabled_segments:
                continue

            segment_data, _ = seg.get_data()
            segment_data["Segment Name"] = self.tree.topLevelItem(idx).text(0)
            values.mission_data.append(segment_data)
        
        values.rcaide_mission = self.create_rcaide_mission()
        # Notify user of successful save
        self._notify("💾 Mission data saved")

    def create_rcaide_mission(self):
        rcaide_mission = RCAIDE.Framework.Mission.Sequential_Segments()
        rcaide_mission.tag = self.mission_name_input.text()
        for idx, seg in enumerate(self.segment_widgets):
            if idx in self.disabled_segments:
                continue

            _, rcaide_segment = seg.get_data()
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
            item.setCheckState(0, Qt.CheckState.Unchecked)
            self.tree.addTopLevelItem(item)

        values.rcaide_mission = self.create_rcaide_mission()


def get_widget(shared_analysis_widget=None) -> QWidget:
    """Factory helper used to create a MissionWidget instance for the tab system."""
    return MissionWidget(shared_analysis_widget)
