# RCAIDE_GUI/tabs/geometry/widgets/powertrain/propulsors/base_propulsor_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame

from common_widgets import DataEntryWidget
from utilities import Units, convert_name, set_data
import rcaide_io


# Field specs are shared as (display label, GUI unit type, RCAIDE attribute path).
# These fields come from RCAIDE's base Propulsor class and apply to every propulsor.
COMMON_PROPULSOR_FIELDS = [
    ("Origin", Units.Position, "origin"),
    ("Active", Units.Boolean, "active"),
    ("Wing Mounted", Units.Boolean, "wing_mounted"),
    ("Sea Level Static Thrust", Units.Force, "sealevel_static_thrust"),
    ("Diameter", Units.Length, "diameter"),
    ("Length", Units.Length, "length"),
    ("Height", Units.Length, "height"),
    ("X-Z Plane Symmetric", Units.Boolean, "xz_plane_symmetric"),
    ("X-Y Plane Symmetric", Units.Boolean, "xy_plane_symmetric"),
    ("Y-Z Plane Symmetric", Units.Boolean, "yz_plane_symmetric"),
]

# Internal-combustion engine settings shared by ICE propulsor variants.
ENGINE_FIELDS = [
    ("Engine", Units.Heading, ""),
    ("Engine Sea Level Power", Units.Unitless, "engine.sea_level_power"),
    ("Engine Flat Rate Altitude", Units.Length, "engine.flat_rate_altitude"),
    ("Engine Rated Speed", Units.Unitless, "engine.rated_speed"),
    ("Engine Power Specific Fuel Consumption", Units.Unitless, "engine.power_specific_fuel_consumption"),
]

# Propeller settings reused by ICE propulsors and turboprops.
PROPELLER_FIELDS = [
    ("Propeller", Units.Heading, ""),
    ("Propeller Number of Blades", Units.Unitless, "propeller.number_of_blades"),
    ("Propeller Tip Radius", Units.Length, "propeller.tip_radius"),
    ("Propeller Hub Radius", Units.Length, "propeller.hub_radius"),
    ("Propeller Blade Pitch Command", Units.Angle, "propeller.blade_pitch_command"),
    ("Propeller Blade Solidity", Units.Unitless, "propeller.blade_solidity"),
    ("Propeller Induced Power Factor", Units.Unitless, "propeller.induced_power_factor"),
    ("Propeller Profile Drag Coefficient", Units.Unitless, "propeller.profile_drag_coefficient"),
    ("Propeller Clockwise Rotation", Units.Boolean, "propeller.clockwise_rotation"),
    ("Propeller Ducted", Units.Boolean, "propeller.ducted"),
]

# Electric motor settings used by electric rotor and electric ducted fan propulsors.
MOTOR_FIELDS = [
    ("Motor", Units.Heading, ""),
    ("Motor Diameter", Units.Length, "motor.diameter"),
    ("Motor Length", Units.Length, "motor.length"),
    ("Motor Resistance", Units.Unitless, "motor.resistance"),
    ("Motor No Load Current", Units.Current, "motor.no_load_current"),
    ("Motor Speed Constant", Units.Unitless, "motor.speed_constant"),
    ("Motor Efficiency", Units.Unitless, "motor.efficiency"),
]

# Electronic speed controller settings used by electric propulsors.
ESC_FIELDS = [
    ("Electronic Speed Controller", Units.Heading, ""),
    ("ESC Bus Voltage", Units.Unitless, "electronic_speed_controller.bus_voltage"),
    ("ESC Efficiency", Units.Unitless, "electronic_speed_controller.efficiency"),
]

# Open-rotor settings used by the electric rotor propulsor.
ROTOR_FIELDS = [
    ("Rotor", Units.Heading, ""),
    ("Rotor Number of Blades", Units.Unitless, "rotor.number_of_blades"),
    ("Rotor Tip Radius", Units.Length, "rotor.tip_radius"),
    ("Rotor Hub Radius", Units.Length, "rotor.hub_radius"),
    ("Rotor Blade Pitch Command", Units.Angle, "rotor.blade_pitch_command"),
    ("Rotor Blade Solidity", Units.Unitless, "rotor.blade_solidity"),
    ("Rotor Induced Power Factor", Units.Unitless, "rotor.induced_power_factor"),
    ("Rotor Profile Drag Coefficient", Units.Unitless, "rotor.profile_drag_coefficient"),
    ("Rotor Clockwise Rotation", Units.Boolean, "rotor.clockwise_rotation"),
    ("Rotor Ducted", Units.Boolean, "rotor.ducted"),
]

# Ducted-fan settings used by the electric ducted fan propulsor.
DUCTED_FAN_FIELDS = [
    ("Ducted Fan", Units.Heading, ""),
    ("Ducted Fan Number of Radial Stations", Units.Count, "ducted_fan.number_of_radial_stations"),
    ("Ducted Fan Number of Rotor Blades", Units.Count, "ducted_fan.number_of_rotor_blades"),
    ("Ducted Fan Tip Radius", Units.Length, "ducted_fan.tip_radius"),
    ("Ducted Fan Hub Radius", Units.Length, "ducted_fan.hub_radius"),
    ("Ducted Fan Exit Radius", Units.Length, "ducted_fan.exit_radius"),
    ("Ducted Fan Blade Clearance", Units.Length, "ducted_fan.blade_clearance"),
    ("Ducted Fan Length", Units.Length, "ducted_fan.length"),
    ("Ducted Fan Effectiveness", Units.Unitless, "ducted_fan.fan_effectiveness"),
]

# Gas-turbine core settings used by the turbojet propulsor.
TURBOJET_COMPONENT_FIELDS = [
    ("Ram", Units.Heading, ""),
    ("Inlet Nozzle", Units.Heading, ""),
    ("Inlet Nozzle Polytropic Efficiency", Units.Unitless, "inlet_nozzle.polytropic_efficiency"),
    ("Inlet Nozzle Pressure Ratio", Units.Unitless, "inlet_nozzle.pressure_ratio"),
    ("Low Pressure Compressor", Units.Heading, ""),
    ("LPC Polytropic Efficiency", Units.Unitless, "low_pressure_compressor.polytropic_efficiency"),
    ("LPC Pressure Ratio", Units.Unitless, "low_pressure_compressor.pressure_ratio"),
    ("High Pressure Compressor", Units.Heading, ""),
    ("HPC Polytropic Efficiency", Units.Unitless, "high_pressure_compressor.polytropic_efficiency"),
    ("HPC Pressure Ratio", Units.Unitless, "high_pressure_compressor.pressure_ratio"),
    ("Low Pressure Turbine", Units.Heading, ""),
    ("LPT Mechanical Efficiency", Units.Unitless, "low_pressure_turbine.mechanical_efficiency"),
    ("LPT Polytropic Efficiency", Units.Unitless, "low_pressure_turbine.polytropic_efficiency"),
    ("High Pressure Turbine", Units.Heading, ""),
    ("HPT Mechanical Efficiency", Units.Unitless, "high_pressure_turbine.mechanical_efficiency"),
    ("HPT Polytropic Efficiency", Units.Unitless, "high_pressure_turbine.polytropic_efficiency"),
    ("Combustor", Units.Heading, ""),
    ("Combustor Pressure Loss Coeff", Units.Unitless, "combustor.alphac"),
    ("Combustor Turbine Inlet Temp", Units.Temperature, "combustor.turbine_inlet_temperature"),
    ("Afterburner", Units.Heading, ""),
    ("Afterburner Pressure Loss Coeff", Units.Unitless, "afterburner.alphac"),
    ("Afterburner Turbine Inlet Temp", Units.Temperature, "afterburner.turbine_inlet_temperature"),
    ("Core Nozzle", Units.Heading, ""),
    ("Core Nozzle Polytropic Efficiency", Units.Unitless, "core_nozzle.polytropic_efficiency"),
    ("Core Nozzle Pressure Ratio", Units.Unitless, "core_nozzle.pressure_ratio"),
]

# Turboprop core settings; propeller fields are appended below for the driven propeller.
TURBOPROP_COMPONENT_FIELDS = [
    ("Compressor", Units.Heading, ""),
    ("Compressor Polytropic Efficiency", Units.Unitless, "compressor.polytropic_efficiency"),
    ("Compressor Pressure Ratio", Units.Unitless, "compressor.pressure_ratio"),
    ("Turbine", Units.Heading, ""),
    ("Turbine Mechanical Efficiency", Units.Unitless, "turbine.mechanical_efficiency"),
    ("Turbine Polytropic Efficiency", Units.Unitless, "turbine.polytropic_efficiency"),
    ("Combustor", Units.Heading, ""),
    ("Combustor Pressure Loss Coeff", Units.Unitless, "combustor.alphac"),
    ("Combustor Turbine Inlet Temp", Units.Temperature, "combustor.turbine_inlet_temperature"),
] + PROPELLER_FIELDS


class BasePropulsorWidget(QWidget):
    # Subclasses fill these in to bind one GUI widget to one RCAIDE propulsor type.
    propulsor_type = ""
    propulsor_class = None
    subcomponent_classes = {}
    type_fields = []

    def __init__(self, index, on_delete, data_values=None):
        super(BasePropulsorWidget, self).__init__()
        # Store the section index so delete callbacks can remove the correct widget.
        self.index = index
        self.on_delete = on_delete

        # Main vertical layout holds name, data-entry fields, divider, and delete button.
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Every propulsor section starts with its editable RCAIDE tag/name.
        name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        name_layout.addWidget(QLabel(f"{self.propulsor_type} Name: "))
        name_layout.addWidget(self.section_name_edit)
        self.main_layout.addLayout(name_layout)

        # Combine fields common to all propulsors with fields from the subclass.
        self.field_specs = COMMON_PROPULSOR_FIELDS + self.type_fields
        self.data_entry_widget = DataEntryWidget([
            (label, units) for label, units, _path in self.field_specs
        ])
        self.main_layout.addWidget(self.data_entry_widget)

        # Divider keeps each propulsor editor visually separated.
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line_bar)

        # Each section owns its delete button, but deletion is handled by the parent frame.
        delete_button = QPushButton(f"Delete {self.propulsor_type}", self)
        delete_button.clicked.connect(self.delete_button_pressed)
        self.main_layout.addWidget(delete_button)

        # Saved aircraft data fills the form; new sections start from RCAIDE defaults.
        if data_values:
            self.load_data_values(data_values)
        else:
            self.load_default_values()

    def delete_button_pressed(self):
        # Delegate removal to the parent layout so sibling indexes can be repaired.
        if self.on_delete is not None:
            self.on_delete(self.index)

    def get_data_values(self):
        # Collect both display-unit data and SI data before creating the RCAIDE object.
        title = self.section_name_edit.text()
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data["Propulsor Tag"] = title
        data["Propulsor Type"] = self.propulsor_type
        data_si["Propulsor Tag"] = title
        data_si["Propulsor Type"] = self.propulsor_type

        rcaide_io.propulsor_names[0].append(convert_name(title))
        return data, self.create_rcaide_structure(data_si)

    def create_rcaide_structure(self, data):
        # Build the RCAIDE propulsor and any required child components first.
        propulsor = self._new_propulsor_with_subcomponents()

        propulsor.tag = data["Propulsor Tag"]
        # Apply each form value to its RCAIDE path, including nested component paths.
        for label, units, path in self.field_specs:
            if units == Units.Heading or not path:
                continue
            self._set_path_if_present(propulsor, path, data[label][0])

        return propulsor

    def load_default_values(self):
        # Instantiate a fresh RCAIDE object so new widgets inherit library defaults.
        propulsor = self._new_propulsor_with_subcomponents()
        self.section_name_edit.setText(propulsor.tag)
        self.data_entry_widget.load_data(self._defaults_to_widget_data(propulsor))

    def load_data_values(self, data):
        # Start from RCAIDE defaults, then overlay whichever saved fields are present.
        default_data = self._defaults_to_widget_data(self._new_propulsor_with_subcomponents())
        default_data.update({
            label: data[label]
            for label, units, _path in self.field_specs
            if units != Units.Heading and label in data
        })
        self.data_entry_widget.load_data(default_data)
        self.section_name_edit.setText(data.get("Propulsor Tag", ""))

    def _new_propulsor_with_subcomponents(self):
        # Create the main RCAIDE propulsor class declared by the subclass.
        propulsor = self.propulsor_class()
        # RCAIDE propulsors default many child components to None; create them here
        # so nested field paths like "motor.efficiency" can be edited immediately.
        for attr_name, component_class in self.subcomponent_classes.items():
            component = component_class()
            component.tag = attr_name
            setattr(propulsor, attr_name, component)
        return propulsor

    def _defaults_to_widget_data(self, propulsor):
        # Convert RCAIDE defaults into the {label: [value, unit_index]} shape DataEntryWidget expects.
        defaults = {}
        for label, units, path in self.field_specs:
            if units == Units.Heading:
                continue
            defaults[label] = [self._get_path_value(propulsor, path), 0]
        return defaults

    @staticmethod
    def _get_path_value(obj, path):
        value = obj
        for key in path.split("."):
            value = value[key]
        return value

    @staticmethod
    def _set_path_if_present(obj, path, value):
        if value is not None:
            set_data(obj, path, value)
