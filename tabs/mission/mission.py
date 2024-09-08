from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget, \
    QTreeWidgetItem

from tabs.mission.widgets import MissionSegmentWidget
from tabs import TabWidget
from utilities import create_scroll_area
import values

import RCAIDE


class MissionWidget(TabWidget):
    def __init__(self):
        super().__init__()
        # Create the main layout
        base_layout = QHBoxLayout(self)
        tree_layout = QVBoxLayout()
        self.main_layout = None
        self.segment_widgets = []

        # Create the mission layout
        mission_layout = QHBoxLayout()
        mission_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add mission name label and input box to the mission layout
        mission_name_label = QLabel("Mission Name:")
        self.mission_name_input = QLineEdit()
        mission_layout.addWidget(mission_name_label)
        mission_layout.addWidget(self.mission_name_input)

        # Create Add Segment Button and Add to Add Segment Button Layout
        add_segment_button = QPushButton("Add New Segment")
        add_segment_button.clicked.connect(self.add_segment)

        # Define Save Data Button
        save_data_button = QPushButton("Save All Data", self)
        save_data_button.clicked.connect(self.save_all_data)

        # Add the Mission Layout, Add Segment Button, and Save Data Button to the left layout
        tree_layout.addLayout(mission_layout)
        tree_layout.addWidget(add_segment_button)
        tree_layout.addWidget(save_data_button)
        tree_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Mission Segments"])

        tree_layout.addWidget(self.tree)

        # Add left layout to the main layout
        base_layout.addLayout(tree_layout, 2)

        layout_scroll = create_scroll_area(self, False)
        base_layout.addLayout(layout_scroll, 6)

        # Add initial segment
        self.add_segment()

    def add_segment(self):
        # Instantiate MissionSectionWidget and add it to mission_segment_layout
        segment_widget = MissionSegmentWidget()
        self.segment_widgets.append(segment_widget)
        self.main_layout.addWidget(segment_widget)

    def save_all_data(self):
        self.tree.clear()

        values.mission_data = []
        values.mission = RCAIDE.Framework.Mission.Sequential_Segments()
        values.mission.tag = self.mission_name_input.text()
        for mission_segment in self.segment_widgets:
            assert isinstance(mission_segment, MissionSegmentWidget)

            segment_data, rcaide_segment = mission_segment.get_data()
            segment_name = segment_data["segment name"]
            values.mission_data.append(segment_data)
            values.mission.append_segment(rcaide_segment)

            new_tree_item = QTreeWidgetItem([segment_name])
            self.tree.addTopLevelItem(new_tree_item)

    def load_from_values(self):
        self.tree.clear()
        for widget in self.segment_widgets:
            widget.deleteLater()

        self.segment_widgets = []
        self.mission_name_input.setText(values.mission_data[0]["segment name"])
        for segment_data in values.mission_data:
            segment_widget = MissionSegmentWidget()
            # segment_widget.create_subsegment_layout(segment_data["subsegment type"])
            segment_widget.load_data(segment_data)
            self.segment_widgets.append(segment_widget)
            self.main_layout.addWidget(segment_widget)
            self.tree.addTopLevelItem(
                QTreeWidgetItem([segment_data["segment name"]]))

            rcaide_segment = segment_widget.create_rcaide_segment()
            values.mission.append_segment(rcaide_segment)

        values.mission = RCAIDE.Framework.Mission.Sequential_Segments()
        values.mission.tag = self.mission_name_input.text()

    def update_layout(self):
        for widget in self.segment_widgets:
            assert isinstance(widget, MissionSegmentWidget)
            widget.update_configs()


# Function to get the widget
def get_widget() -> QWidget:
    return MissionWidget()
