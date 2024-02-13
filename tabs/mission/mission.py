import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QLineEdit, QPushButton, QScrollArea, QApplication


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Create the main layout
        main_layout = QHBoxLayout(self)

        # Create the left side layout for Mission
        left_layout = QVBoxLayout()

        # Create the mission layout
        mission_layout = QHBoxLayout()

        # Align mission_layout to the top of left_layout
        mission_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add mission name label and input box to the mission layout
        mission_name_label = QLabel("Mission Name:")
        self.mission_name_input = QLineEdit()
        mission_layout.addWidget(mission_name_label)
        mission_layout.addWidget(self.mission_name_input)

        # Add mission layout to the left layout
        left_layout.addLayout(mission_layout)

        # Create Horizontal Layout for Append Button
        append_button = QPushButton("Add New Segment")
        append_button.clicked.connect(self.append_section)
        left_layout.addWidget(append_button)

        

        # Add left layout to the main layout
        main_layout.addLayout(left_layout, 2)

        # Create a scroll area for the right side (segments)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Create a widget to contain the segments layout
        self.segments_widget = QWidget()
        self.segments_layout = QVBoxLayout(self.segments_widget)
        self.scroll_area.setWidget(self.segments_widget)

        # Add scroll area to the main layout
        main_layout.addWidget(self.scroll_area, 6)

        # Add initial segment
        self.add_segment()

        # Set up the base widget
        self.setWindowTitle("Mission Manager")
        self.resize(800, 600)

    def add_segment(self):
        # Create the vertical layout for the segment
        segment_layout = QVBoxLayout()

        # Create each horizontal layout for the segment name and type
        segment_name = QHBoxLayout()
        segment_type = QHBoxLayout()

        # Add segment name label and input box
        segment_name_label = QLabel("Segment Name:")
        segment_name_input = QLineEdit()
        segment_name.addWidget(segment_name_label)
        segment_name.addWidget(segment_name_input)

        # Add segment type label and nested dropdown
        segment_type_label = QLabel("Segment Type:")
        nested_dropdown = self.create_nested_dropdown()  # Call method to create nested dropdown
        segment_type.addWidget(segment_type_label)
        segment_type.addLayout(nested_dropdown)

        # Add delete button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.delete_segment(segment_layout))
        segment_type.addWidget(delete_button)

        # Adding Horizontal Layouts to Vertical Layout
        segment_layout.addLayout(segment_name)
        segment_layout.addLayout(segment_type)

        # Add the segment layout to the segments layout
        self.segments_layout.addLayout(segment_layout)

    def populate_nested_dropdown(self, index, nested_dropdown):
        nested_dropdown.clear()
        options = ["Climb", "Descent, Cruise"]
        nested_options = [["Climb 1", "Climb 2", "Climb 3"], ["Descent 1", "Descent 2", "Descent 3"], ["Cruise 1", "Cruise 2", "Cruise 3"]]
        nested_dropdown.addItems(nested_options[index])

    def create_nested_dropdown(self):
        top_dropdown = QComboBox()
        top_dropdown.addItems(['Climb', 'Desent', 'Cruise'])
        nested_dropdown = QComboBox()

        # Connect top dropdown index change to populate the nested dropdown
        top_dropdown.currentIndexChanged.connect(lambda index, nd=nested_dropdown: self.populate_nested_dropdown(index, nd))

        layout = QHBoxLayout()
        layout.addWidget(top_dropdown)
        layout.addWidget(nested_dropdown)

        return layout

    def delete_segment(self, segment_layout):
        """Delete the segment layout."""
        try:
            # Remove all widgets from the segment layout
            while segment_layout.count():
                item = segment_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            # Remove the segment layout from the segments layout
            self.segments_layout.removeItem(segment_layout)
        except Exception as e:
            print(f"An error occurred while deleting segment layout: {e}")

    def append_section(self):
        """Append a new segment."""
        self.add_segment()


# Function to get the widget
def get_widget() -> QWidget:
    return MyWidget()
