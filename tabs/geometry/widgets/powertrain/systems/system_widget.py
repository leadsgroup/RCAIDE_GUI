# RCAIDE_GUI/tabs/geometry/widgets/powertrain/systems/system_widget.py
#
# Created:  Jun 2026, M. Clarke

import RCAIDE
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFrame, QComboBox)
from common_widgets import DataEntryWidget
from utilities import Units

_SYSTEM_TYPES = [
    "Avionics",
    "Auxiliary Power Unit",
    "Cabin Loads",
    "Electrical",
    "Environmental Controls",
    "Flight Controls",
    "Furnishings",
    "Hydraulics",
    "Ice Protection",
    "Instruments",
    "Water Tank",
]

_TYPE_TO_RCAIDE = {
    "Avionics":                RCAIDE.Library.Components.Powertrain.Systems.Avionics,
    "Auxiliary Power Unit":    RCAIDE.Library.Components.Powertrain.Systems.Auxiliary_Power_Unit,
    "Cabin Loads":             RCAIDE.Library.Components.Powertrain.Systems.Cabin_Loads,
    "Electrical":              RCAIDE.Library.Components.Powertrain.Systems.Electrical,
    "Environmental Controls":  RCAIDE.Library.Components.Powertrain.Systems.Environmental_Controls,
    "Flight Controls":         RCAIDE.Library.Components.Powertrain.Systems.Flight_Controls,
    "Furnishings":             RCAIDE.Library.Components.Powertrain.Systems.Furnishings,
    "Hydraulics":              RCAIDE.Library.Components.Powertrain.Systems.Hydraulics,
    "Ice Protection":          RCAIDE.Library.Components.Powertrain.Systems.Ice_Protection,
    "Instruments":             RCAIDE.Library.Components.Powertrain.Systems.Instruments,
    "Water Tank":              RCAIDE.Library.Components.Powertrain.Systems.Water_Tank,
}


class SystemWidget(QWidget):
    def __init__(self, index, on_delete, data_values=None):
        super().__init__()
        self.index = index
        self.on_delete = on_delete

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Type selector row
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("System Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(_SYSTEM_TYPES)
        self.type_combo.setFixedWidth(220)
        type_row.addWidget(self.type_combo)
        type_row.addStretch()
        main_layout.addLayout(type_row)

        # Name row
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        name_row.addWidget(self.name_edit)
        main_layout.addLayout(name_row)

        # Data fields
        data_units_labels = [
            ("Origin",            Units.Position),
            ("Power Draw",        Units.Power),
            ("Uninstalled Mass",  Units.Mass),
        ]
        self.data_entry_widget = DataEntryWidget(data_units_labels)
        main_layout.addWidget(self.data_entry_widget)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        delete_btn = QPushButton("Delete System", self)
        delete_btn.clicked.connect(self._on_delete)
        main_layout.addWidget(delete_btn)

        if data_values:
            self.load_data_values(data_values)

    def _on_delete(self):
        if self.on_delete:
            self.on_delete(self.index)

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data["System Type"] = self.type_combo.currentText()
        data["System Name"] = self.name_edit.text()
        data_si["System Type"] = data["System Type"]
        data_si["System Name"] = data["System Name"]
        return data, self._build_rcaide(data_si)

    def _build_rcaide(self, data):
        cls = _TYPE_TO_RCAIDE.get(data["System Type"],
                                  RCAIDE.Library.Components.Powertrain.Systems.Systems)
        system = cls()
        system.tag = data["System Name"] or system.tag
        origin = data.get("Origin", [[[0, 0, 0]], 0])
        if isinstance(origin, list) and len(origin) == 2:
            origin = origin[0]
        system.origin = origin if isinstance(origin[0], list) else [origin]
        system.power_draw = data.get("Power Draw", [0, 0])
        if isinstance(system.power_draw, list):
            system.power_draw = system.power_draw[0]
        mass = data.get("Uninstalled Mass", [0, 0])
        if isinstance(mass, list):
            mass = mass[0]
        system.mass_properties.uninstalled = mass
        return system

    def load_data_values(self, data):
        system_type = data.get("System Type", "Avionics")
        idx = self.type_combo.findText(system_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.name_edit.setText(data.get("System Name", ""))
        self.data_entry_widget.load_data(data)
