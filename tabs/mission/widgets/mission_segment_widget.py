import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QLineEdit, QPushButton, QScrollArea

class MissionSegmentWidget(QWidget):
    def __init__(self):
        super().__init__() 

        # Create the vertical layout for the segment
        self.segment_layout = QVBoxLayout()

        # Align the entire segment_layout to the top
        self.segment_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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
        
        # Create a button
        delete_button = QPushButton('Delete', self)

        # Connect the button's clicked signal to a function
        delete_button.clicked.connect(self.deleteWidget)

        # Add the button to the segment type layout
        segment_type.addWidget(delete_button)
        
        # Adding Horizontal Layouts to Vertical Layout
        self.segment_layout.addLayout(segment_name)
        self.segment_layout.addLayout(segment_type)

        # Align segment type layout to top of segment_layout
        segment_type.setAlignment(Qt.AlignmentFlag.AlignTop) 

        # Set the layout of the widget as segment_layout
        self.setLayout(self.segment_layout)

        # Create subsegment layout for initial subsegment type and add it to the segment layout
        initial_subsegment_type = "Constant CAS/Constant Rate"  # You can set your initial subsegment type here
        self.create_subsegment_layout(initial_subsegment_type)

    # Trying to make sure labels more than 4 get a new row but having clearing problems    
    """
    def create_subsegment_layout(self, subsegment_type):
        print("Creating subsegment layout for type:", subsegment_type)
        
        # Clear any existing layout for subsegment type
        self.clear_subsegment_type_layout()

        # Get data fields for the selected subsegment type from the dictionary
        data_fields = self.subsegment_data_fields.get(subsegment_type, [])

        # Add QLineEdit boxes for each data field
        label_count = len(data_fields)
        max_labels_per_row = 4
        current_row_layout = None
        self.subsegment_layout = QVBoxLayout()  # Initialize or reuse the existing layout

        for i, field in enumerate(data_fields):
            print("Adding QLineEdit for field:", field)
            label = QLabel(field)
            line_edit = QLineEdit()

            # Check if it's the first label or the current row is full
            if i % max_labels_per_row == 0:
                current_row_layout = QHBoxLayout()
                self.subsegment_layout.addLayout(current_row_layout)

            # Add label and line edit to the current row layout
            current_row_layout.addWidget(label)
            current_row_layout.addWidget(line_edit)

        # Add the subsegment layout to the segments layout
        self.segment_layout.addLayout(self.subsegment_layout)
        print("Subsegment layout created and added.")

        # Align subsegment layout to top
        self.subsegment_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def clear_subsegment_type_layout(self):
        # Clear any existing layout for subsegment type
        if hasattr(self, 'subsegment_layout'):
            while self.subsegment_layout.count():
                item = self.subsegment_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
    """

    def create_subsegment_layout(self, subsegment_type):
        print("Creating subsegment layout for type:", subsegment_type)
        # Clear any existing layout for subsegment type
        self.clear_subsegment_type_layout()

        # Create a layout for the selected subsegment type
        self.subsegment_layout = QHBoxLayout()

        # Get data fields for the selected subsegment type from the dictionary
        data_fields = self.subsegment_data_fields.get(subsegment_type, [])

        # Add QLineEdit boxes for each data field
        for field in data_fields:
            print("Adding QLineEdit for field:", field)
            label = QLabel(field)
            line_edit = QLineEdit()
            self.subsegment_layout.addWidget(label)
            self.subsegment_layout.addWidget(line_edit)
        
        #Set the subsegment layout as an attribute
        self.subsegment_layout = self.subsegment_layout

        # Add the subsegment layout to the segments layout
        self.segment_layout.addLayout(self.subsegment_layout)
        print("Subsegment layout created and added.")

        # Align subsegment layout to top
        self.subsegment_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
 
    def clear_subsegment_type_layout(self):
        # Clear any existing layout for subsegment type
        if hasattr(self, 'subsegment_layout'):
            layout = self.subsegment_layout
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            self.subsegment_layout = None
            #self.segment_layout.removeItem(layout)
    
  
    def populate_nested_dropdown(self, index, nested_dropdown):
        nested_dropdown.clear()
        options = ["Climb", "Cruise", "Descent", "Ground", "Single_Point", "Transition", "Vertical Flight"]
        nested_options = [["Constant CAS/Constant Rate", "Constant Dynamic Pressure/Constant Angle", "Constant EAS/Constant Rate", "Constant Mach/Constant Angle", "Constant Mach/Constant Rate", "Constant Mach/Linear Altitude", "Constant Speed/Constant Angle Noise", "Constant Speed/Constant Angle", "Constant Speed/Constant Rate", "Constant Speed/Linear Altitude", "Constant Throttle/Constant Speed", "Linear Mach/Constant Rate", "Linear Speed/Constant Rate"], 
                        ["Constant Acceleration/Constant Altitude", "Constant Dynamic Pressure/Constant Altitude Loiter", "Constant Mach/Constant Altitude", "Constant Pitch Rate/Constant Altitude", "Constant Speed/Constant Altitude Loiter", "Constant Speed/Constant Altitude", "Constant Throttle/Constant Altitude"], 
                        ["Constant CAS/Constant Rate", "Constant EAS/Constant Rate", "Constant Speed/Constant Angle Noise", "Constant Speed/Constant Angle", "Constant Speed/Constant Rate", "Linear Mach/Constant Rate", "Linear Speed/Constant Rate"], 
                        ["Battery Discharge", "Battery Recharge", "Ground", "Landing", "Takeoff"], 
                        ["Set Speed/Set Altitude/No Propulsion", "Set Speed/Set Altitude", "Set Speed/Set Throttle"], 
                        ["Constant Acceleration/Constant Angle/Linear Climb", "Constant Acceleration/Constant Pitchrate/Constant Altitude"],
                        ["Climb", "Descent", "Hover"]]
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

    def deleteWidget(self):
       # delete widget 
        self.deleteLater()

    # Dictionary to map subsegment types to their corresponding data fields
    subsegment_data_fields = {
        # Climb Subsegments
        "Constant CAS/Constant Rate": ["Altitude Start:", "Altitude End:", "Climb Rate:", "CAS:", "True Course Angle:"],
        "Constant Dynamic Pressure/Constant Angle": ["Altitude Start:", "Altitude End:", "Climb Angle:", "Dynamic Pressure", "True Course Angle"],
        "Constant Dynamic Pressure/Constant Rate": ["Altitude Start:", "Altitude End:", "Climb Angle:", "Dynamic Pressure", "True Course Angle"],
        "Constant EAS/Constant Rate": ["Altitude Start:", "Altitude End:", "Climb Rate", "EAS", "True Course Angle"],
        "Constant Mach/Constant Angle": ["Altitude Start:", "Altitude End:", "Climb Angle",  "True Course Angle"],
        "Constant Mach/Constant Rate": ["Altitude Start:", "Altitude End:", "Climb Rate", "Mach Number", "True Course Angle"], 
        "Constant Mach/Linear Altitude": ["Mach Number", "Distance", "Altitude Start:", "Altitude End:",   "True Course Angle"],
        "Constant Speed/Constant Angle Noise": ["Altitude Start", "Altitude End", "Climb Angle", "Air Speed", "True Course Speed"], 
        "Constant Speed/Constant Angle": ["Altitude Start", "Altitude End", "Climb Angle", "Air Speed", "True Course Speed"], 
        "Constant Speed/Constant Rate": ["Altitude Start", "Altitude End", "Climb Rate", "Speed", "True Course Angle"],
        "Constant Speed/Linear Altitude": ["Air Speed", "Distance", "Altitude Start", "Altitude End", "True Course Angle"],
        "Constant Throttle/Constant Speed": ["Altitude Start", "Altitude End", "Throttle", "Air Speed", "True Course Angle"], 
        "Linear Mach/Constant Rate": ["Altitude Start", "Altitude End", "Climb Rate", "Mach Number End", "Mach Number Start", "True Course Angle"],
        "Linear Speed/Constant Rate": ["Altitude Start", "Altitude End", "Climb Rate", "Air Speed Start", "Air Speed End", "True Course Angle"], 


        # Cruise Subsegments
        "Constant Acceleration/Constant Altitude": ["Altitude", "Acceleration", "Air Speed Start", "Air Speed End", "True Course Angle"], 
        "Constant Dynamic Pressure/Constant Altitude Loiter": ["Altitude", "Dynamic Pressure", "Time", "True Course Angle"],
        "Constant Dynamics Pressure/Constant Altitude": ["Altitude", "Acceleration", "Air Speed Start", "Air Speed End", "True Course Angle"], 
        "Constant Mach/Constant Altitude Loiter": ["Altitude", "Mach Number", "Time", "True Course Angle"],
        "Constant Mach/Constant Altitude": ["Altitude", "Mach Number", "Distance", "True Course Angle"],
        "Constant Pitch Rate/Constant Altitude": ["Altitude", "Pitch Rate", "Pitch Initial", "Pitch Final", "True Course Angle"], 
        "Constant Speed/Constant Altitude Loiter": ["Altitude", "Air Speed", "Time", "True Course Angle"],
        "Constant Speed/Constant Altitude": ["Altitude", "Air Speed", "Distance", "True Course Angle"],
        "Constant Throttle/Constant Altitude": ["Throttle", "Altitude", "Air Speed Start", "Air Speed End", "True Course Angle"],

        # Descent Subsegments
        "Constant CAS/Constant Rate": ["Altitude Start", "Altitude End", "Descent Rate", "Calibrated Airspeed", "True Course Angle"],
        "Constant EAS/Constant Rate": ["Altitude Start", "Altitude End", "Descent Rate", "Equivalent Air Speed", "True Course Angle"], 
        "Constant Speed/Constant Angle Noise": ["Altitude Start", "Altitude End", "Descent Angle", "Air Speed", "True Course Angle"], 
        "Constant Speed/Constant Angle": ["Altitude Start", "Altitude End", "Descent Angle", "Air Speed", "True Course Angle"],
        "Constant Speed/Constant Rate": ["Altitude Start", "Altitude End", "Descent Rate", "Air Speed", "True Course Angle"],
        "Linear Mach/Constant Rate": ["Altitude Start", "Altitude End", "Descent Rate", "Mach Number End", "Mach Number Start", "True Course Angle"],
        "Linear Speed/Constant Rate": ["Altitude Start", "Altitude End", "Descent Rate", "Air Speed Start", "Air Speed End", "True Course Angle"],

        # Ground Subsegments
        "Battery Discharge": ["Altitude", "Time", "Current", "Overcharge Contingency", "True Course Angle"],
        "Battery Recharge": ["Altitude", "Time", "Current", "Overcharge Contingency", "True Course Angle"],
        "Ground": ["Ground Incline", "Friction Coefficient", "Throttle", "Velocity Start", "Velocity End", "Altitude", "True Course Angle"],
        "Landing": ["Ground Incline", "Velocity Start", "Velocity End", "Friction Coefficient", "Throttle", "Altitude", "True Course Angle"],
        "Takeoff": ["Ground Incline", "Velocity Start", "Velocity End", "Friction Coefficient", "Throttle", "Altitude", "True Course Angle"],

        # Single Point Subsegments
        "Set Speed/Set Altitude/No Propulsion": ["Altitude", "Air Speed", "Distance", "Acceleration Z", "True Course Angle"],
        "Set Speed/Set Altitude": ["Altitude", "Air Speed", "Distance", "Acceleration X", "Acceleration Z", "State Numerics Number of Control Points"],
        "Set Speed/Set Throttle": ["Altitude", "Air Speed", "Throttle", "Acceleration Z", "True Course Angle"],

        # Transition Subsegments
        "Constant Acceleration/Constant Angle/Linear Climb": ["Altitude Start", "Altitude End", "Air Speed Start", "Climb Angle", "Acceleration", "Pitch Initial", "Pitch Final", "True Course Angle"],
        "Constant Acceleration/Constant Pitchrate/Constant Altitude": ["Altitude", "Acceleration",  "Air Speed Start", "Air Speed End", "Pitch Initial", "Pitch Final", "True Course Angle"],

        # Vertical Flight Subsegments 
        "Climb": ["Altitude Start", "Altitude End", "Climb Rate", "True Course Angle"], 
        "Descent": ["Altitude Start", "Altitude End", "Descent Rate", "True Course Angle"], 
        "Hover": ["Altitude", "Time", "True Course Angle"]
        }
