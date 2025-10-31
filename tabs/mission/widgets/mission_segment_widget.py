from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QLineEdit
from PyQt6.lupdate import user

from tabs.mission.widgets.flight_controls_widget import FlightControlsWidget
from tabs.mission.widgets.mission_segment_helper import segment_data_fields, segment_rcaide_classes
from utilities import Units, create_line_bar, clear_layout, set_data, convert_name
import values
from widgets import DataEntryWidget


class MissionSegmentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Create the vertical layout for the segment
        self.segment_layout = QVBoxLayout()
        self.subsegment_layout = QVBoxLayout()
        self.dof_layout = QVBoxLayout()
        self.top_dropdown = QComboBox()
        self.nested_dropdown = QComboBox()
        self.subsegment_entry_widget = None
        self.flight_controls_widget : FlightControlsWidget = None
        self.dof_entry_widget : DataEntryWidget = None

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
        # Clear any existing subsegment layout
        clear_layout(self.subsegment_layout)
        clear_layout(self.dof_layout)

        # Get data fields for the selected subsegment type from the dictionary
        data_fields = segment_data_fields[self.top_dropdown.currentIndex()].get(
            subsegment_type, [])

        # Initialize or reuse the existing layout
        self.subsegment_layout = QVBoxLayout()
        self.config_layout = QHBoxLayout()

        self.update_configs()
        self.subsegment_layout.addLayout(self.config_layout)

        self.subsegment_entry_widget = DataEntryWidget(data_fields)
        self.subsegment_layout.addWidget(self.subsegment_entry_widget)

        self.subsegment_layout.addWidget(
            QLabel("<b>Select Degrees of Freedom</b>"))
        self.subsegment_layout.addWidget(create_line_bar())

        dof_fields = [("Forces in X axis", Units.Boolean, "flight_dynamics.force_x"),
                      ("Moments about X axis", Units.Boolean, "flight_dynamics.moment_x"),
                      ("Forces in Y axis", Units.Boolean, "flight_dynamics.force_y"),
                      ("Moments about Y axis", Units.Boolean, "flight_dynamics.moment_y"),
                      ("Forces in Z axis", Units.Boolean, "flight_dynamics.force_z"),
                      ("Moments about Z axis", Units.Boolean, "flight_dynamics.moment_z")]

        self.dof_entry_widget = DataEntryWidget(dof_fields)
        self.dof_layout.addWidget(self.dof_entry_widget)
        self.subsegment_layout.addLayout(self.dof_layout)

        # Add the subsegment layout to the segments layout
        self.segment_layout.addLayout(self.subsegment_layout)

        # Align subsegment layout to top
        self.subsegment_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.subsegment_layout.addWidget(
            QLabel("<b>Select Flight Controls</b>"))
        self.subsegment_layout.addWidget(create_line_bar())
        
        self.flight_controls_widget = FlightControlsWidget()
        self.subsegment_layout.addWidget(self.flight_controls_widget)
        self.subsegment_layout.addWidget(create_line_bar())

    def populate_nested_dropdown(self, index, nested_dropdown):
        nested_dropdown.clear()
        # options = ["Climb", "Cruise", "Descent", "Ground",
        #            "Single_Point", "Transition", "Vertical Flight"]
        nested_options = [segment_type.keys()
                          for segment_type in segment_data_fields]
        nested_dropdown.addItems(nested_options[index])

    def create_nested_dropdown(self):
        self.top_dropdown.addItems(["Climb", "Cruise", "Descent", "Ground",
                                    "Single_Point", "Transition", "Vertical Flight"])

        self.nested_dropdown = QComboBox()

        # Call populate_nested_dropdown to populate the nested dropdown based on the initial index
        self.populate_nested_dropdown(0, self.nested_dropdown)

        # Add label for subsegment type
        subsegment_type_label = QLabel('Sub Segment Type:')

        # Connect top dropdown index change to populate the nested dropdown
        self.top_dropdown.currentIndexChanged.connect(
            lambda index, nd=self.nested_dropdown: self.populate_nested_dropdown(index, nd))

        # Connect nested dropdown index change to create subsegment layout
        self.nested_dropdown.currentIndexChanged.connect(
            lambda index, nd=self.nested_dropdown: self.create_subsegment_layout(nd.currentText()))

        layout = QHBoxLayout()
        layout.addWidget(self.top_dropdown)
        layout.addWidget(subsegment_type_label)
        layout.addWidget(self.nested_dropdown)

        return layout

    def delete_widget(self):
        self.deleteLater()

    def get_data(self):
        assert self.subsegment_entry_widget is not None and isinstance(
            self.subsegment_entry_widget, DataEntryWidget)
        
        data = self.subsegment_entry_widget.get_values()
        data["segment name"] = self.segment_name_input.text()
        data["flight forces"] = self.dof_entry_widget.get_values()
        data["flight controls"] = self.flight_controls_widget.get_data()
        data["top dropdown"] = self.top_dropdown.currentIndex()
        data["nested dropdown"] = self.nested_dropdown.currentText()
        data["config"] = self.config_selector.currentIndex()
                
        rcaide_segment = self.create_rcaide_segment()
        return data, rcaide_segment
    
    def load_data(self, data):
        self.top_dropdown.setCurrentIndex(data["top dropdown"])
        self.nested_dropdown.setCurrentText(data["nested dropdown"])

        assert self.subsegment_entry_widget is not None and isinstance(
            self.subsegment_entry_widget, DataEntryWidget)
        self.subsegment_entry_widget.load_data(data)
        self.segment_name_input.setText(data["segment name"])
        
        assert self.dof_entry_widget is not None and isinstance(
            self.dof_entry_widget, DataEntryWidget)
        self.dof_entry_widget.load_data(data["flight forces"])
        
        self.flight_controls_widget.load_data(data["flight controls"])

    def update_configs(self):
        clear_layout(self.config_layout)

        config_names = [config["config name"]
                        for config in values.config_data]
        self.config_selector = QComboBox()
        self.config_selector.addItems(config_names)
        self.config_layout.addWidget(QLabel("Aircraft Configuration: "), 3)
        self.config_layout.addWidget(self.config_selector, 7)

    def create_rcaide_segment(self):
        segment = segment_rcaide_classes[self.top_dropdown.currentIndex(
        )][self.nested_dropdown.currentText()]()
        segment.tag = self.segment_name_input.text()

        assert self.subsegment_entry_widget is not None and isinstance(
            self.subsegment_entry_widget, DataEntryWidget)
        values_si = self.subsegment_entry_widget.get_values_si()

        for data_unit_label in self.subsegment_entry_widget.data_units_labels:
            rcaide_label = data_unit_label[-1]
            user_label = data_unit_label[0]
            set_data(segment, rcaide_label, values_si[user_label][0])
        
        assert self.dof_entry_widget is not None and isinstance(
            self.dof_entry_widget, DataEntryWidget)
        dof_values = self.dof_entry_widget.get_values()
        
        for data_unit_label in self.dof_entry_widget.data_units_labels:
            rcaide_label = data_unit_label[-1]
            user_label = data_unit_label[0]
            set_data(segment, rcaide_label, dof_values[user_label][0])
        
        self.flight_controls_widget.set_control_variables(segment)
        
        config_tag = convert_name(self.config_selector.currentText())
        analyses = values.rcaide_analyses[config_tag]
        segment.analyses.extend(analyses)
        
        return segment
