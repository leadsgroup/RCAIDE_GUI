from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QLineEdit

from tabs.mission.widgets.flight_controls_widget import FlightControlsWidget
from utilities import Units, create_line_bar
from widgets import DataEntryWidget


class MissionSegmentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Create the vertical layout for the segment
        self.segment_layout = QVBoxLayout()
        self.subsegment_layout = QVBoxLayout()
        self.dof_layout = QVBoxLayout()
        self.top_dropdown = QComboBox()

        # Align the entire segment_layout to the top
        self.segment_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create each horizontal layout for the segment name and type
        segment_name = QHBoxLayout()
        segment_type = QHBoxLayout()

        # Add segment name label and input box
        segment_name_label = QLabel("Segment Name:")
        self.segment_name_input = QLineEdit()
        segment_name.addWidget(segment_name_label)
        segment_name.addWidget(self.segment_name_input)

        # Add segment type label and nested dropdown
        segment_type_label = QLabel("Segment Type:")
        # Call method to create nested dropdown
        nested_dropdown = self.create_nested_dropdown()
        segment_type.addWidget(segment_type_label)
        segment_type.addLayout(nested_dropdown)

        # TODO: Add aircraft configuration dropdown

        # Adding Horizontal Layouts to Vertical Layout
        self.segment_layout.addLayout(segment_name)
        self.segment_layout.addLayout(segment_type)

        # Align segment type layout to top of segment_layout
        segment_type.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Set the layout of the widget as segment_layout
        self.setLayout(self.segment_layout)

        # Create subsegment layout for initial subsegment type and add it to the segment layout
        # You can set your initial subsegment type here
        initial_subsegment_type = "Constant CAS/Constant Rate"
        self.create_subsegment_layout(initial_subsegment_type)

    # Trying to make sure labels more than 4 get a new row but having clearing problems
    def create_subsegment_layout(self, subsegment_type):
        print("Creating subsegment layout for type:", subsegment_type)

        # Clear any existing subsegment layout
        self.clear_layout(self.subsegment_layout)
        print("Cleared existing subsegment layout.")
        self.clear_layout(self.dof_layout)

        # Get data fields for the selected subsegment type from the dictionary
        data_fields = self.subsegment_data_fields[self.top_dropdown.currentIndex()].get(
            subsegment_type, [])

        # Initialize or reuse the existing layout
        self.subsegment_layout = QVBoxLayout()

        subsegment_entry_widget = DataEntryWidget(data_fields)
        self.subsegment_layout.addWidget(subsegment_entry_widget)

        self.subsegment_layout.addWidget(
            QLabel("<b>Select Degrees of Freedom</b>"))
        self.subsegment_layout.addWidget(create_line_bar())

        dof_fields = [("Forces in X axis", Units.Boolean),
                      ("Moments about X axis", Units.Boolean),
                      ("Forces in Y axis", Units.Boolean),
                      ("Moments about Y axis", Units.Boolean),
                      ("Forces in Z axis", Units.Boolean),
                      ("Moments about Z axis", Units.Boolean)]

        dof_entry_widget = DataEntryWidget(dof_fields)
        self.dof_layout.addWidget(dof_entry_widget)
        self.subsegment_layout.addLayout(self.dof_layout)

        # Add the subsegment layout to the segments layout
        self.segment_layout.addLayout(self.subsegment_layout)
        print("Subsegment layout created and added.")

        # Align subsegment layout to top
        self.subsegment_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.subsegment_layout.addWidget(
            QLabel("<b>Select Flight Controls</b>"))
        self.subsegment_layout.addWidget(create_line_bar())
        self.subsegment_layout.addWidget(FlightControlsWidget())

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    # Remove widget
                    widget.deleteLater()
                else:
                    sublayout = item.layout()
                    if sublayout is not None:
                        # Recursively clear sublayout
                        self.clear_layout(sublayout)

    def populate_nested_dropdown(self, index, nested_dropdown):
        nested_dropdown.clear()
        # options = ["Climb", "Cruise", "Descent", "Ground",
        #            "Single_Point", "Transition", "Vertical Flight"]
        nested_options = [
            ["Constant CAS/Constant Rate", "Constant Dynamic Pressure/Constant Angle", "Constant EAS/Constant Rate",
             "Constant Mach/Constant Angle", "Constant Mach/Constant Rate", "Constant Mach/Linear Altitude",
             "Constant Speed/Constant Angle Noise", "Constant Speed/Constant Angle", "Constant Speed/Constant Rate",
             "Constant Speed/Linear Altitude", "Constant Throttle/Constant Speed", "Linear Mach/Constant Rate",
             "Linear Speed/Constant Rate"],
            ["Constant Acceleration/Constant Altitude", "Constant Dynamic Pressure/Constant Altitude Loiter",
             "Constant Mach/Constant Altitude",
             "Constant Pitch Rate/Constant Altitude", "Constant Speed/Constant Altitude Loiter",
             "Constant Speed/Constant Altitude", "Constant Throttle/Constant Altitude"],
            ["Constant CAS/Constant Rate", "Constant EAS/Constant Rate", "Constant Speed/Constant Angle Noise",
             "Constant Speed/Constant Angle", "Constant Speed/Constant Rate", "Linear Mach/Constant Rate",
             "Linear Speed/Constant Rate"],
            ["Battery Discharge", "Battery Recharge",
             "Ground", "Landing", "Takeoff"],
            ["Set Speed/Set Altitude/No Propulsion",
             "Set Speed/Set Altitude", "Set Speed/Set Throttle"],
            ["Constant Acceleration/Constant Angle/Linear Climb",
             "Constant Acceleration/Constant Pitchrate/Constant Altitude"],
            ["Climb", "Descent", "Hover"]]
        nested_dropdown.addItems(nested_options[index])

    def create_nested_dropdown(self):
        self.top_dropdown.addItems(["Climb", "Cruise", "Descent", "Ground",
                                    "Single_Point", "Transition", "Vertical Flight"])

        nested_dropdown = QComboBox()

        # Call populate_nested_dropdown to populate the nested dropdown based on the initial index
        self.populate_nested_dropdown(0, nested_dropdown)

        # Add label for subsegment type
        subsegment_type_label = QLabel('Sub Segment Type:')

        # Connect top dropdown index change to populate the nested dropdown
        self.top_dropdown.currentIndexChanged.connect(
            lambda index, nd=nested_dropdown: self.populate_nested_dropdown(index, nd))

        # Connect nested dropdown index change to create subsegment layout
        nested_dropdown.currentIndexChanged.connect(
            lambda index, nd=nested_dropdown: self.create_subsegment_layout(nd.currentText()))

        layout = QHBoxLayout()
        layout.addWidget(self.top_dropdown)
        layout.addWidget(subsegment_type_label)
        layout.addWidget(nested_dropdown)

        return layout

    def delete_widget(self):
        # delete widget
        self.deleteLater()

    def get_data(self):
        data = {"segment name": self.segment_name_input.text()}

        return data

    # Dictionary to map subsegment types to their corresponding data fields
    subsegment_data_fields = [{
        # Climb Subsegments
        "Constant CAS/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                       ("Climb Rate", Units.Velocity), ("CAS",
                                                                        Units.Velocity),
                                       ("True Course Angle", Units.Angle)],
        "Constant Dynamic Pressure/Constant Angle": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                                     ("Climb Angle", Units.Angle), (
                                                         "Dynamic Pressure", Units.Pressure),
                                                     ("True Course Angle", Units.Angle)],
        "Constant Dynamic Pressure/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                                    ("Climb Angle", Units.Angle), (
                                                        "Dynamic Pressure", Units.Pressure),
                                                    ("True Course Angle", Units.Angle)],
        "Constant EAS/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                       ("Climb Rate", Units.Velocity), ("EAS",
                                                                        Units.Velocity),
                                       ("True Course Angle", Units.Angle)],
        "Constant Mach/Constant Angle": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                         ("Climb Angle", Units.Angle), ("True Course Angle", Units.Angle)],
        "Constant Mach/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                        ("Climb Rate", Units.Velocity), ("Mach Number",
                                                                         Units.Unitless),
                                        ("True Course Angle", Units.Angle)],
        "Constant Mach/Linear Altitude": [("Mach Number", Units.Unitless), ("Distance", Units.Length),
                                          ("Altitude Start",
                                           Units.Length), ("Altitude End", Units.Length),
                                          ("True Course Angle", Units.Unitless)],
        "Constant Speed/Constant Angle Noise": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                                ("Climb Angle", Units.Angle), ("Air Speed",
                                                                               Units.Velocity),
                                                ("True Course Speed", Units.Velocity)],
        "Constant Speed/Constant Angle": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                          ("Climb Angle", Units.Angle), ("Air Speed",
                                                                         Units.Velocity),
                                          ("True Course Speed", Units.Velocity)],
        "Constant Speed/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                         ("Climb Rate", Units.Velocity), ("Speed",
                                                                          Units.Velocity),
                                         ("True Course Angle", Units.Unitless)],
        "Constant Speed/Linear Altitude": [("Air Speed", Units.Velocity), ("Distance", Units.Length),
                                           ("Altitude Start",
                                            Units.Length), ("Altitude End", Units.Length),
                                           ("True Course Angle", Units.Unitless)],
        "Constant Throttle/Constant Speed": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                             ("Throttle", Units.Unitless), ("Air Speed",
                                                                            Units.Velocity),
                                             ("True Course Angle", Units.Unitless)],
        "Linear Mach/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                      ("Climb Rate", Units.Velocity), ("Mach Number End",
                                                                       Units.Unitless),
                                      ("Mach Number Start", Units.Unitless), ("True Course Angle", Units.Unitless)],
        "Linear Speed/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                       ("Climb Rate", Units.Velocity), ("Air Speed Start",
                                                                        Units.Velocity),
                                       ("Air Speed End", Units.Velocity), ("True Course Angle", Units.Unitless)],
    }, {
        # Cruise Subsegments
        "Constant Acceleration/Constant Altitude": [("Altitude", Units.Length), ("Acceleration", Units.Acceleration),
                                                    ("Air Speed Start",
                                                     Units.Velocity),
                                                    ("Air Speed End",
                                                     Units.Velocity),
                                                    ("True Course Angle", Units.Angle)],
        "Constant Dynamic Pressure/Constant Altitude Loiter": [("Altitude", Units.Length),
                                                               ("Dynamic Pressure",
                                                                Units.Pressure),
                                                               ("Time", Units.Time),
                                                               ("True Course Angle", Units.Angle)],
        "Constant Dynamics Pressure/Constant Altitude": [("Altitude", Units.Length),
                                                         ("Acceleration",
                                                          Units.Acceleration),
                                                         ("Air Speed Start",
                                                          Units.Velocity),
                                                         ("Air Speed End",
                                                          Units.Velocity),
                                                         ("True Course Angle", Units.Angle)],
        "Constant Mach/Constant Altitude Loiter": [("Altitude", Units.Length), ("Mach Number", Units.Unitless),
                                                   ("Time", Units.Time), ("True Course Angle", Units.Angle)],
        "Constant Mach/Constant Altitude": [("Altitude", Units.Length), ("Mach Number", Units.Unitless),
                                            ("Distance", Units.Length), ("True Course Angle", Units.Angle)],
        "Constant Pitch Rate/Constant Altitude": [("Altitude", Units.Length), ("Pitch Rate", Units.Velocity),
                                                  ("Pitch Initial", Units.Angle), (
                                                      "Pitch Final", Units.Angle),
                                                  ("True Course Angle", Units.Angle)],
        "Constant Speed/Constant Altitude Loiter": [("Altitude", Units.Length), ("Air Speed", Units.Velocity),
                                                    ("Time", Units.Time), ("True Course Angle", Units.Angle)],
        "Constant Speed/Constant Altitude": [("Altitude", Units.Length), ("Air Speed", Units.Velocity),
                                             ("Distance", Units.Length), ("True Course Angle", Units.Angle)],
        "Constant Throttle/Constant Altitude": [("Throttle", Units.Unitless), ("Altitude", Units.Length),
                                                ("Air Speed Start", Units.Velocity), (
                                                    "Air Speed End", Units.Velocity),
                                                ("True Course Angle", Units.Angle)],
    }, {
        # Descent Subsegments
        "Constant CAS/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                       ("Descent Rate", Units.Velocity), ("CAS",
                                                                          Units.Velocity),
                                       ("True Course Angle", Units.Angle)],
        "Constant EAS/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                       ("Descent Rate", Units.Velocity), ("EAS",
                                                                          Units.Velocity),
                                       ("True Course Angle", Units.Angle)],
        "Constant Speed/Constant Angle Noise": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                                ("Descent Angle", Units.Unitless), (
                                                    "Air Speed", Units.Velocity),
                                                ("True Course Angle", Units.Angle)],
        "Constant Speed/Constant Angle": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                          ("Descent Angle",
                                           Units.Unitless), ("Air Speed", Units.Velocity),
                                          ("True Course Angle", Units.Angle)],
        "Constant Speed/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                         ("Descent Rate", Units.Velocity), ("Air Speed",
                                                                            Units.Velocity),
                                         ("True Course Angle", Units.Angle)],
        "Linear Mach/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                      ("Descent Rate", Units.Velocity), (
                                          "Mach Number End", Units.Unitless),
                                      ("Mach Number Start", Units.Unitless), ("True Course Angle", Units.Angle)],
        "Linear Speed/Constant Rate": [("Altitude Start", Units.Length), ("Altitude End", Units.Length),
                                       ("Descent Rate", Units.Velocity), (
                                           "Air Speed Start", Units.Velocity),
                                       ("Air Speed End", Units.Velocity), ("True Course Angle", Units.Angle)],
    }, {
        # Ground Subsegments
        "Climb": [("Altitude Start", Units.Length), ("Altitude End", Units.Length), ("Climb Rate", Units.Velocity),
                  ("True Course Angle", Units.Angle)],
        "Descent": [("Altitude Start", Units.Length), ("Altitude End", Units.Length), ("Descent Rate", Units.Velocity),
                    ("True Course Angle", Units.Angle)],
        "Hover": [("Altitude", Units.Length), ("Time", Units.Time), ("True Course Angle", Units.Angle)]
    }, {
        # Single Point Subsegments
        "Set Speed/Set Altitude/No Propulsion": [("Altitude", Units.Length), ("Air Speed", Units.Velocity),
                                                 ("Distance", Units.Length), (
                                                     "Acceleration Z", Units.Acceleration),
                                                 ("True Course Angle", Units.Angle)],
        "Set Speed/Set Altitude": [("Altitude", Units.Length), ("Air Speed", Units.Velocity),
                                   ("Distance", Units.Length), ("Acceleration X",
                                                                Units.Acceleration),
                                   ("Acceleration Z", Units.Acceleration),
                                   ("State Numerics Number of Control Points", Units.Unitless)],
        "Set Speed/Set Throttle": [("Altitude", Units.Length), ("Air Speed", Units.Velocity),
                                   ("Throttle", Units.Unitless), ("Acceleration Z",
                                                                  Units.Acceleration),
                                   ("True Course Angle", Units.Angle)],
    }, {
        # Transition Subsegments
        "Constant Acceleration/Constant Angle/Linear Climb": [("Altitude Start", Units.Length),
                                                              ("Altitude End",
                                                               Units.Length),
                                                              ("Air Speed Start",
                                                               Units.Velocity),
                                                              ("Climb Angle",
                                                               Units.Unitless),
                                                              ("Acceleration",
                                                               Units.Acceleration),
                                                              ("Pitch Initial",
                                                               Units.Angle),
                                                              ("Pitch Final",
                                                               Units.Angle),
                                                              ("True Course Angle", Units.Angle)],
        "Constant Acceleration/Constant Pitchrate/Constant Altitude": [("Altitude", Units.Length),
                                                                       ("Acceleration",
                                                                        Units.Acceleration),
                                                                       ("Air Speed Start",
                                                                        Units.Velocity),
                                                                       ("Air Speed End",
                                                                        Units.Velocity),
                                                                       ("Pitch Initial",
                                                                        Units.Angle),
                                                                       ("Pitch Final",
                                                                        Units.Angle),
                                                                       ("True Course Angle", Units.Angle)],
    }, {
        # Vertical Flight Subsegments
        "Climb": [("Altitude Start", Units.Length), ("Altitude End", Units.Length), ("Climb Rate", Units.Velocity),
                  ("True Course Angle", Units.Angle)],
        "Descent": [("Altitude Start", Units.Length), ("Altitude End", Units.Length), ("Descent Rate", Units.Velocity),
                    ("True Course Angle", Units.Angle)],
        "Hover": [("Altitude", Units.Length), ("Time", Units.Time), ("True Course Angle", Units.Angle)]
    }]
