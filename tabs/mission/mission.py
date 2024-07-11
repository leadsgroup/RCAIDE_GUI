from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QTreeWidget

from tabs.mission.widgets import MissionSegmentWidget


class MissionWidget(QWidget):
    def __init__(self, geometry_widget):
        super().__init__()

        self.geometry_widget = geometry_widget

        # Create the main layout
        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()

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
        left_layout.addLayout(mission_layout)
        left_layout.addWidget(add_segment_button)
        left_layout.addWidget(save_data_button)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        tree = QTreeWidget()
        tree.setColumnCount(1)
        tree.setHeaderLabels(["Mission Segments"])

        left_layout.addWidget(tree)

        # Add left layout to the main layout
        main_layout.addLayout(left_layout, 2)

        # Create a scroll area for the right side (segments)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a widget to contain the layout
        scroll_content = QWidget()

        # Create a layout for the scroll area
        self.mission_segment_layout = QVBoxLayout()

        # Set the layout of the scroll content widget
        scroll_content.setLayout(self.mission_segment_layout)

        # Set the widget containing the layout as the scroll area's widget
        scroll_area.setWidget(scroll_content)

        # Add scroll area to the main layout
        main_layout.addWidget(scroll_area, 6)

        # Add initial segment
        self.add_segment()

        # Set up the base widget
        self.setWindowTitle("Mission Manager")
        self.resize(800, 600)

    def add_segment(self):
        # Instantiate MissionSectionWidget and add it to mission_segment_layout
        segment_widget = MissionSegmentWidget()
        self.mission_segment_layout.addWidget(segment_widget)

    def save_all_data(self):
        pass

    def update_layout(self):
        pass

# Function to get the widget


def get_widget() -> QWidget:
    return MissionWidget(None)
