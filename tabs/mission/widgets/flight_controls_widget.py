from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget, QCheckBox, QSizePolicy

from utilities import Units, create_line_bar, set_data
from widgets import DataEntryWidget
import values


class FlightControlsWidget(QWidget):
    def __init__(self):
        super().__init__()
        base_layout = QVBoxLayout()

        toggles_layout = QHBoxLayout()
        self.data_entry_widgets = []
        for key, toggles in self.fields.items():
            sub_layout = QVBoxLayout()

            header = QLabel("<b>" + key + "</b>")
            header.setSizePolicy(QSizePolicy.Policy.Minimum,
                                 QSizePolicy.Policy.Minimum)
            sub_layout.addWidget(header)
            sub_layout.addWidget(create_line_bar())

            self.data_entry_widgets.append(DataEntryWidget(toggles, 1))
            sub_layout.addWidget(self.data_entry_widgets[-1])

            toggles_layout.addLayout(sub_layout, 1)

        base_layout.addLayout(toggles_layout)

        self.setLayout(base_layout)
    
    def get_data(self):
        data = {}
        for widget in self.data_entry_widgets:
            assert isinstance(widget, DataEntryWidget)
            data.update(widget.get_values())
            
        return data
    
    def load_data(self, data):
        for widget in self.data_entry_widgets:
            assert isinstance(widget, DataEntryWidget)
            widget.load_data(data)
    
    def set_control_variables(self, segment):
        for widget in self.data_entry_widgets:
            assert isinstance(widget, DataEntryWidget)
            
            data_units_labels = widget.data_units_labels
            data = widget.get_values()
            for data_unit_label in data_units_labels:
                rcaide_label = data_unit_label[-1]
                user_label = data_unit_label[0]

                set_data(segment, rcaide_label, data[user_label][0])
        
        segment.assigned_control_variables.throttle.assigned_propulsors = values.propulsor_names
            

    fields = {
        "Autopilot": [
            ("Body Angle", Units.Boolean, "assigned_control_variables.body_angle.active"),
            ("Bank Angle", Units.Boolean, "assigned_control_variables.bank_angle.active"),
            ("Wind Angle", Units.Boolean, "assigned_control_variables.wind_angle.active"),
            ("Velocity", Units.Boolean, "assigned_control_variables.velocity.active"),
            ("Acceleration", Units.Boolean, "assigned_control_variables.acceleration.active"),
            ("Altitude", Units.Boolean, "assigned_control_variables.altitude.active"),
        ],
        "Control Surfaces": [
            ("Elevator Deflection", Units.Boolean, "assigned_control_variables.elevator_deflection.active"),
            ("Rudder Deflection", Units.Boolean, "assigned_control_variables.rudder_deflection.active"),
            ("Flap Deflection", Units.Boolean, "assigned_control_variables.flap_deflection.active"),
            ("Slat Deflection", Units.Boolean, "assigned_control_variables.slat_deflection.active"),
            ("Aileron Deflection", Units.Boolean, "assigned_control_variables.aileron_deflection.active"),
        ],
        "Propulsion": [
            ("Throttle", Units.Boolean, "assigned_control_variables.throttle.active"),
            ("Thrust Vector Angle", Units.Boolean, "assigned_control_variables.thrust_vector_angle.active"),
            # ("Blade Pitch Angle", Units.Boolean, "assigned_control_variables.blade_pitch_angle.active"),
        ]
    }
