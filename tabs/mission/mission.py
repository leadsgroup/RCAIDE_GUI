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

        # Dictionary to map subsegment types to their corresponding data fields
        self.subsegment_data_fields = {
            # Climb Subsegments
            "Constant CAS/Constant Rate": ["Altitude Start:", "Altitude End:", "Climb Rate:", "CAS:", "True Course Angle:"],
            "Constant Dynamic Pressure/Constant Angle": ["Altitude Start:", "Altitude End:", "Climb Angle:", "Dynamic Pressure", "True Course Angle"],
            "Constant Dynamic Pressure/Constant Rate": ["Altitude Start:", "Altitude End:", "Climb Angle:", "Dynamic Pressure", "True Course Angle"],
            "Constant EAS/Constant Rate": ["Altitude Start:", "Altitude End:", "Climb Rate", "EAS", "True Course Angle"],
            "Constant Mach/Constant Angle": ["Altitude Start:", "Altitude End:", "Climb Rate", "Mach Number", "True Course Angle"],

            # Cruise Subsegments
            "Constant Acceleration/Constant Altitude": ["Altitude", "Acceleration", "Air Speed Start", "Air Speed End", "True Course Angle"], 
            "Constant Dynamic Pressure/Constant Altitude Loiter": ["Altitude", "Dynamic Pressure", "Time", "True Course Angle"],
            "Constant Dynamics Pressure/Constant Altitude": ["Altitude", "Acceleration", "Air Speed Start", "Air Speed End", "True Course Angle"]

            # Descent Subsegments

            #Ground Subsegments

            #Single Point Subsegments

            #Transition Subsegments

            #Vertical Flight Subsegments

            
        }

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
        self.segment_layout = QVBoxLayout()

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
        delete_button.clicked.connect(lambda: self.delete_segment(self.segment_layout))
        segment_type.addWidget(delete_button)

        # Adding Horizontal Layouts to Vertical Layout
        self.segment_layout.addLayout(segment_name)
        self.segment_layout.addLayout(segment_type)

        # Add the segment layout to the segments layout
        self.segments_layout.addLayout(self.segment_layout)

        # Create the subsegment layout for the initial subsegment type
        #initial_subsegment_type = nested_dropdown.itemText(0)  # Get the initial subsegment type
        #self.create_subsegment_layout(initial_subsegment_type)

    def create_subsegment_layout(self, subsegment_type):
        print("Creating subsegment layout for type:", subsegment_type)
        # Clear any existing layout for subsegment type
        self.clear_subsegment_type_layout()

        # Create a layout for the selected subsegment type
        subsegment_layout = QHBoxLayout()

        # Get data fields for the selected subsegment type from the dictionary
        data_fields = self.subsegment_data_fields.get(subsegment_type, [])

        # Add QLineEdit boxes for each data field
        for field in data_fields:
            print("Adding QLineEdit for field:", field)
            label = QLabel(field)
            line_edit = QLineEdit()
            subsegment_layout.addWidget(label)
            subsegment_layout.addWidget(line_edit)

        # Set the subsegment layout as an attribute
        self.subsegment_layout = subsegment_layout

        # Add the subsegment layout to the segments layout
        self.segments_layout.addLayout(self.subsegment_layout)
        print("Subsegment layout created and added.")

    def clear_subsegment_type_layout(self):
        # Clear any existing layout for subsegment type
        if hasattr(self, 'subsegment_layout'):
            layout = self.subsegment_layout
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            self.segments_layout.removeItem(layout)

    def populate_nested_dropdown(self, index, nested_dropdown):
        nested_dropdown.clear()
        options = ["Climb", "Cruise", "Descent", "Ground", "Single_Point", "Transition", "Vertical Flight"]
        nested_options = [["Constant CAS/Constant Rate", "Constant Dynamic Pressure/Constant Angle", "Constant EAS/Constant Rate", "Constant Mach/Constant Angle", "Constant Mach/Constant Rate", "Constant Mach/Linear Altitude", "Constant Speed/Constant Angle/Noise", "Constant Speed/Constant Angle", "Constant Speed/Constant Rate", "Constant Speed/Linear Altitude", "Constant Throttle/Constant Speed", "Linear Mach/Constant Rate", "Linear Speed/Constant Rate"], 
                          ["Constant Acceleration/Constant Altitude", "Constant Dynamic Pressure/Constant Altitude Loiter", "Constant Mach/Constant Altitude", "Constant Pitch Rate/Constant Altitude", "Constant Speed/Constant Altitude Loiter", "Constant Speed/Constant Altitude", "Constant Throttle/Constant Altitude"], 
                          ["Constant CAS/Constant_Rate", "Constant EAS/Constant Rate", "Constant Speed/Constant Angle/Noise", "Constant Speed/Constant Angle", "Constant Speed/Constant Rate", "Linear Mach/Constant Rate", "Linear Speed/Constant Rate"], 
                          ["Battery Discharge", "Battery Recharge", "Ground", "Landing", "Takeoff"], 
                          ["Set Speed/Set Altitude/No Propulsion", "Set Speed/Set Altitude", "Set Speed/Set Throttle"], 
                          ["Constant Acceleration/Constant Angle/Linear Climb", "Constant Acceleration/Constant Pitchrate/Constant Altitude"],
                          ["Climb", "Desent", "Hover"]]
        nested_dropdown.addItems(nested_options[index])

    def create_nested_dropdown(self):
        top_dropdown = QComboBox()
        top_dropdown.addItems(["Climb", "Cruise", "Descent", "Ground", "Single_Point", "Transition", "Vertical Flight"])
        nested_dropdown = QComboBox()

        # Call populate_nested_dropdown to populate the nested dropdown based on the initial index
        self.populate_nested_dropdown(0, nested_dropdown)

        # Add label for subsegment type
        subsegment_type_label = QLabel('Sub Segment Type:')

        # Connect top dropdown index change to populate the nested dropdown
        top_dropdown.currentIndexChanged.connect(lambda index, nd=nested_dropdown: self.populate_nested_dropdown(index, nd))

        # Connect nested dropdown index change to create subsegment layout
        nested_dropdown.currentIndexChanged.connect(lambda index, nd=nested_dropdown: self.create_subsegment_layout(nd.currentText()))

        layout = QHBoxLayout()
        layout.addWidget(top_dropdown)
        layout.addWidget(subsegment_type_label)
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
            self.segments_layout.removeItem(self.segment_layout)
        except Exception as e:
            print(f"An error occurred while deleting segment layout: {e}")

    def append_section(self):
        """Append a new segment."""
        self.add_segment()


# Function to get the widget
def get_widget() -> QWidget:
    return MyWidget()
