# RCAIDE_GUI/tabs/geometry/widgets/powertrain/systems/system_widget.py
#
# Created:  Jun 2026, M. Clarke

import RCAIDE
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFrame, QComboBox, QSizePolicy)
from common_widgets import DataEntryWidget
from utilities import Units
import rcaide_io

_SYSTEM_TYPES = [
    "Generic System",
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
    "Generic System":          RCAIDE.Library.Components.Powertrain.Systems.Systems,
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
        # RCAIDE component loaded from a file (stripped JSON dict); None for a new system
        self.loaded_component = None

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

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
        if self.loaded_component is not None:
            data["rcaide_component"] = self.loaded_component
        return data, self.create_rcaide_structure(data_si)

    def base_system(self):
        """Return the loaded RCAIDE system if it is still the selected type, else a new one."""
        cls = _TYPE_TO_RCAIDE[self.type_combo.currentText()]
        if self.loaded_component is not None:
            system = rcaide_io.component_from_dict(self.loaded_component)
            if type(system) is cls:
                return system
        return cls()

    def create_rcaide_structure(self, data_si):
        # Start from the loaded system so settings the form does not show are kept
        system = self.base_system()
        system.tag = self.name_edit.text() or system.tag
        if data_si["Origin"][0] is not None:
            system.origin = data_si["Origin"][0]
        if data_si["Power Draw"][0] is not None:
            system.power_draw = data_si["Power Draw"][0]
        # Only some RCAIDE systems (e.g. Avionics) carry an uninstalled mass
        if "uninstalled_mass" in system and data_si["Uninstalled Mass"][0] is not None:
            system.uninstalled_mass = data_si["Uninstalled Mass"][0]
        return system

    def load_data_values(self, data):
        self.loaded_component = data.get("rcaide_component")
        idx = self.type_combo.findText(data.get("System Type", "Avionics"))
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.name_edit.setText(data.get("System Name", ""))

        # Read the form from the loaded system, then overlay saved fields
        system = self.base_system()
        form_data = {
            "Origin":           [system.origin, 0],
            "Power Draw":       [system.power_draw, 0],
            "Uninstalled Mass": [system.get("uninstalled_mass"), 0],
        }
        form_data.update({k: v for k, v in data.items() if k in form_data})
        self.data_entry_widget.load_data(form_data)
