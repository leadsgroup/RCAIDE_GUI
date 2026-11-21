# RCAIDE_GUI/tabs/geometry/widgets/powertrain/converters/converter_widget.py

# Created: Nov 2026, M. Clarke

import RCAIDE
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy

from common_widgets import DataEntryWidget
from utilities import Units, BTN_STYLE, set_if_changed, get_path_value
import rcaide_io

_Converters = RCAIDE.Library.Components.Powertrain.Converters

# GUI converter type -> RCAIDE converter class
CONVERTER_CLASSES = {
    "Turboelectric Generator": _Converters.Turboelectric_Generator,
    "DC Motor":                _Converters.DC_Motor,
    "Pump":                    _Converters.Pump,
    "Heater":                  _Converters.Heater,
    "PEM Fuel Cell":           _Converters.Proton_Exchange_Membrane_Fuel_Cell,
}

# Form fields shared by every converter: (display label, GUI unit type, RCAIDE attribute path)
COMMON_CONVERTER_FIELDS = [
    ("Origin", Units.Position, "origin"),
    ("Active", Units.Boolean,  "active"),
]

# Form fields specific to each converter type
CONVERTER_FIELDS = {
    "Turboelectric Generator": [
        ("Power Split Ratio", Units.Unitless, "power_split_ratio"),
    ],
    "DC Motor": [
        ("Efficiency",                      Units.Unitless, "efficiency"),
        ("Resistance (ohm)",                Units.Unitless, "resistance"),
        ("No Load Current",                 Units.Current,  "no_load_current"),
        ("Speed Constant",                  Units.Unitless, "speed_constant"),
        ("Design Angular Velocity (rad/s)", Units.Unitless, "design_angular_velocity"),
        ("Design Torque (N-m)",             Units.Unitless, "design_torque"),
    ],
    "Pump": [
        ("Efficiency",             Units.Unitless, "efficiency"),
        ("Design Inlet Pressure",  Units.Pressure, "design_inlet_pressure"),
        ("Design Outlet Pressure", Units.Pressure, "design_outlet_pressure"),
        ("Power Density (W/kg)",   Units.Unitless, "power_density"),
        ("Turbine Efficiency",     Units.Unitless, "turbine_efficiency"),
        ("Distributor Split",      Units.Unitless, "distributor_split"),
    ],
    "Heater": [
        ("Efficiency",   Units.Unitless, "efficiency"),
        ("Design Power", Units.Power,    "design_power"),
    ],
    "PEM Fuel Cell": [
        ("Series Cells",              Units.Count,       "electrical_configuration.series"),
        ("Parallel Cells",            Units.Count,       "electrical_configuration.parallel"),
        ("Normal Cell Count",         Units.Count,       "geometric_configuration.normal_count"),
        ("Parallel Cell Count",       Units.Count,       "geometric_configuration.parallel_count"),
        ("Stack Temperature",         Units.Temperature, "fuel_cell.stack_temperature"),
        ("Rated Current Density",     Units.Unitless,    "fuel_cell.rated_current_density"),
        ("Air Excess Ratio",          Units.Unitless,    "fuel_cell.air_excess_ratio"),
    ],
}


class ConverterWidget(QWidget):
    """Editor for one RCAIDE network converter.

    The converter loaded from a file is kept and the form fields are applied on
    top of it, so settings the form does not show (fuel cell model constants,
    a heater's assigned tank, a turboelectric generator's turboshaft) are kept.
    """

    def __init__(self, index, on_delete, data_values=None, converter_type="Turboelectric Generator"):
        super().__init__()
        self.index = index
        self.on_delete = on_delete
        data_values = data_values or {}
        self.converter_type = data_values.get("Converter Type", converter_type)
        # RCAIDE component loaded from a file (stripped JSON dict); None for a new converter
        self.loaded_component = data_values.get("rcaide_component")
        self.field_specs = COMMON_CONVERTER_FIELDS + CONVERTER_FIELDS.get(self.converter_type, [])

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel(f"{self.converter_type} Name:"))
        self.section_name_edit = QLineEdit(self)
        name_row.addWidget(self.section_name_edit)
        delete_button = QPushButton("Delete", self)
        delete_button.setStyleSheet(BTN_STYLE)
        delete_button.setMaximumWidth(80)
        delete_button.clicked.connect(self.delete_button_pressed)
        name_row.addWidget(delete_button)
        layout.addLayout(name_row)

        self.data_entry_widget = DataEntryWidget([(label, units) for label, units, _path in self.field_specs])
        layout.addWidget(self.data_entry_widget)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        self.load_data_values(data_values)

    def base_converter(self):
        """Return the loaded RCAIDE converter, or a new one with RCAIDE defaults."""
        if self.loaded_component is not None:
            return rcaide_io.component_from_dict(self.loaded_component)
        return CONVERTER_CLASSES[self.converter_type]()

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data["Converter Name"] = self.section_name_edit.text()
        data["Converter Type"] = self.converter_type
        if self.loaded_component is not None:
            data["rcaide_component"] = self.loaded_component
        return data, self.create_rcaide_structure(data_si)

    def create_rcaide_structure(self, data_si):
        # Start from the loaded converter so settings the form does not show are kept
        converter = self.base_converter()
        converter.tag = self.section_name_edit.text() or converter.tag
        for label, units, path in self.field_specs:
            set_if_changed(converter, path, data_si[label][0])
        return converter

    def load_data_values(self, data):
        # Read the form from the loaded converter (or RCAIDE defaults), then overlay saved fields
        converter = self.base_converter()
        form_data = {label: data.get(label, [get_path_value(converter, path), 0])
                     for label, _units, path in self.field_specs}
        self.data_entry_widget.load_data(form_data)
        self.section_name_edit.setText(data.get("Converter Name", converter.tag))

    def delete_button_pressed(self):
        if self.on_delete is not None:
            self.on_delete(self.index)
