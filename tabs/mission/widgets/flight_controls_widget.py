from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QSizePolicy,
)

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
            header.setSizePolicy(
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Minimum,
            )
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

        # Assign all active propulsors to the throttle control variable
        assigned = values.propulsor_names
        available = self._fallback_propulsor_names()
        if not assigned or not assigned[0]:
            assigned = [available]
            values.propulsor_names = assigned
        elif available and not set(assigned[0]).issubset(set(available)):
            assigned = [available]
            values.propulsor_names = assigned

        segment.assigned_control_variables.throttle.assigned_propulsors = assigned

        # If throttle control is enabled for this segment
        if getattr(
            segment.assigned_control_variables.throttle,
            "active",
            False,
        ):
            # Check that initial guesses are supported
            if hasattr(
                segment.assigned_control_variables.throttle,
                "initial_guess_values",
            ):
                # Provide a default throttle guess if none is set
                if not segment.assigned_control_variables.throttle.initial_guess_values:
                    segment.assigned_control_variables.throttle.initial_guess_values = [
                        [0.7]
                    ]

        # If body angle (angle of attack) control is enabled
        if getattr(
            segment.assigned_control_variables.body_angle,
            "active",
            False,
        ):
            # Check that initial guesses are supported
            if hasattr(
                segment.assigned_control_variables.body_angle,
                "initial_guess_values",
            ):
                # Provide a default body angle guess if none is set
                if not segment.assigned_control_variables.body_angle.initial_guess_values:
                    segment.assigned_control_variables.body_angle.initial_guess_values = [
                        [0.0]
                    ]

    def set_defaults(self, throttle=False, body_angle=False):
        # Enable required control variables so the solver can trim the segment
        for widget in self.data_entry_widgets:
            assert isinstance(widget, DataEntryWidget)

            defaults = {}

            # Loop through each control variable defined in the widget
            for label, _, rcaide_label in widget.data_units_labels:
                label_lower = rcaide_label.lower()
                value = False

                # Enable throttle control if this segment needs thrust
                if "throttle.active" in label_lower:
                    value = throttle

                # Enable body angle control if this segment needs trim
                elif "body_angle.active" in label_lower:
                    value = body_angle

                # Store the default enabled/disabled state
                defaults[label] = (value, 0)

            # Apply the default control settings to the UI
            widget.load_data(defaults)

    def _fallback_propulsor_names(self):
        # Store unique propulsor names
        names = []

        # Get RCAIDE aircraft configurations
        cfgs = getattr(values, "rcaide_configs", None)

        # Exit if configurations are missing or invalid
        if not isinstance(cfgs, dict):
            return names

        # Loop through each aircraft configuration
        for cfg in cfgs.values():
            # Loop through propulsion networks in the configuration
            for network in getattr(cfg, "networks", []):
                # Loop through propulsors in the network
                for propulsor in getattr(network, "propulsors", []):
                    # Extract the propulsor tag if it exists
                    tag = getattr(propulsor, "tag", None)
                    # Add unique propulsor tags only
                    if tag and tag not in names:
                        names.append(tag)

        # Return the collected propulsor names
        return names

    fields = {
        "Kinematics": [
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
        ],
    }
