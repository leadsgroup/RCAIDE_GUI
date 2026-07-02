# RCAIDE_GUI/tabs/mission/widgets/flight_controls_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QSizePolicy,
)

from utilities import Units, create_line_bar, set_data
from common_widgets import DataEntryWidget
import rcaide_io

# ------------------------------------------------------------------------------
# Flight Controls Widget
# ------------------------------------------------------------------------------
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

        # Propulsor assignment checkboxes
        base_layout.addWidget(QLabel("<b>Assigned Propulsors</b>"))
        base_layout.addWidget(create_line_bar())

        self.propulsor_checkboxes = {}
        self._prop_row = QHBoxLayout()
        self._build_propulsor_checkboxes()
        base_layout.addLayout(self._prop_row)

        self.setLayout(base_layout)

    # -------------------------------------------------------------------------
    # Propulsor checkboxes
    # -------------------------------------------------------------------------
    def _build_propulsor_checkboxes(self):
        while self._prop_row.count():
            item = self._prop_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.propulsor_checkboxes.clear()

        names = []
        try:
            names = rcaide_io.propulsor_names[0] or []
        except (AttributeError, IndexError, TypeError):
            pass

        for name in names:
            cb = QCheckBox(name)
            cb.setChecked(True)
            self.propulsor_checkboxes[name] = cb
            self._prop_row.addWidget(cb)

        self._prop_row.addStretch(1)

    def refresh_propulsors(self):
        """Rebuild propulsor checkboxes from the current rcaide_io.propulsor_names."""
        self._build_propulsor_checkboxes()

    # -------------------------------------------------------------------------
    # Data access
    # -------------------------------------------------------------------------
    def get_data(self):
        data = {}
        for widget in self.data_entry_widgets:
            assert isinstance(widget, DataEntryWidget)
            data.update(widget.get_values())
        data["assigned_propulsors"] = [
            name for name, cb in self.propulsor_checkboxes.items() if cb.isChecked()
        ]
        return data

    def load_data(self, data):
        for widget in self.data_entry_widgets:
            assert isinstance(widget, DataEntryWidget)
            widget.load_data(data)

        selected = data.get("assigned_propulsors", [])
        # Handle [value, 0] unit-arg format that may appear when loading from RCAIDE JSON
        if (isinstance(selected, list) and len(selected) == 2
                and isinstance(selected[1], int) and not isinstance(selected[1], bool)):
            selected = selected[0] if isinstance(selected[0], list) else []

        for name, cb in self.propulsor_checkboxes.items():
            cb.setChecked(not selected or name in selected)

    def set_control_variables(self, segment):
        for widget in self.data_entry_widgets:
            assert isinstance(widget, DataEntryWidget)
            data_units_labels = widget.data_units_labels
            data = widget.get_values()
            for data_unit_label in data_units_labels:
                rcaide_label = data_unit_label[-1]
                user_label = data_unit_label[0]
                set_data(segment, rcaide_label, data[user_label][0])

        # Use the propulsors the user checked; fall back to all available propulsors
        selected = [name for name, cb in self.propulsor_checkboxes.items() if cb.isChecked()]
        if not selected:
            selected = list(self.propulsor_checkboxes.keys())
        if not selected:
            # Last-resort fallback: derive names from vehicle networks
            try:
                for network in rcaide_io.rcaide_vehicle.networks:
                    for prop in network.propulsors:
                        if prop.tag not in selected:
                            selected.append(prop.tag)
            except Exception:
                pass

        segment.assigned_control_variables.throttle.assigned_propulsors = [selected]

        if getattr(segment.assigned_control_variables.thrust_vector_angle, "active", False):
            segment.assigned_control_variables.thrust_vector_angle.assigned_propulsors = [selected]

        if getattr(segment.assigned_control_variables.blade_pitch_command, "active", False):
            rotor_tags = []
            try:
                for network in rcaide_io.rcaide_vehicle.networks:
                    for prop in network.propulsors:
                        rotor = getattr(prop, 'rotor', None)
                        if rotor is not None and hasattr(rotor, 'tag'):
                            rotor_tags.append(rotor.tag)
            except Exception:
                pass
            if rotor_tags:
                segment.assigned_control_variables.blade_pitch_command.assigned_rotors = [rotor_tags]

        if getattr(segment.assigned_control_variables.throttle, "active", False):
            if hasattr(segment.assigned_control_variables.throttle, "initial_guess_values"):
                if not segment.assigned_control_variables.throttle.initial_guess_values:
                    segment.assigned_control_variables.throttle.initial_guess_values = [[0.7]]

        if getattr(segment.assigned_control_variables.pitch_angle, "active", False):
            if hasattr(segment.assigned_control_variables.pitch_angle, "initial_guess_values"):
                if not segment.assigned_control_variables.pitch_angle.initial_guess_values:
                    segment.assigned_control_variables.pitch_angle.initial_guess_values = [[0.0]]

    def set_defaults(self, throttle=False, pitch_angle=False):
        for widget in self.data_entry_widgets:
            assert isinstance(widget, DataEntryWidget)
            defaults = {}
            for label, _, rcaide_label in widget.data_units_labels:
                label_lower = rcaide_label.lower()
                value = False
                if "throttle.active" in label_lower:
                    value = throttle
                elif "pitch_angle.active" in label_lower:
                    value = pitch_angle
                defaults[label] = (value, 0)
            widget.load_data(defaults)

    fields = {
        "Kinematics": [
            ("Pitch Angle", Units.Boolean, "assigned_control_variables.pitch_angle.active"),
            ("Bank Angle", Units.Boolean, "assigned_control_variables.bank_angle.active"),
            ("Angle of Attack", Units.Boolean, "assigned_control_variables.angle_of_attack.active"),
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
        ],
    }
