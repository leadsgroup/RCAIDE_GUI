# RCAIDE_GUI/tabs/geometry/widgets/powertrain/distributors/electrical_bus_widget.py

# Created: Jun 2026, M. Clarke

import RCAIDE
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame, QSizePolicy

from tabs.geometry.widgets.powertrain.distributors.base_distributor_widget import BaseDistributorWidget
from common_widgets import DataEntryWidget
from utilities import Units, BTN_STYLE


class ElectricalBusWidget(BaseDistributorWidget):
    distributor_type = "Electrical Bus"

    def __init__(self, index, on_delete, data_values=None):
        super().__init__(index, on_delete)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.addWidget(QLabel("Bus Name:"))
        self.section_name_edit = QLineEdit(self)
        row.addWidget(self.section_name_edit)
        del_btn = QPushButton("Delete", self)
        del_btn.setStyleSheet(BTN_STYLE)
        del_btn.setMaximumWidth(80)
        del_btn.clicked.connect(self.delete_button_pressed)
        row.addWidget(del_btn)
        layout.addLayout(row)

        self.data_entry_widget = DataEntryWidget([
            ("Efficiency",        Units.Unitless),
            ("Voltage",           Units.Unitless),
            ("Power Split Ratio", Units.Unitless),
            ("Charging C-Rate",   Units.Unitless),
        ])
        layout.addWidget(self.data_entry_widget)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        if data_values:
            self.load_data_values(data_values)

    def get_data_values(self):
        fields = self.data_entry_widget.get_values()
        data = {
            "distributor name":  self.section_name_edit.text(),
            "distributor_type":  "Electrical Bus",
            "Efficiency":        fields.get("Efficiency",        [1.0, 0]),
            "Voltage":           fields.get("Voltage",           [0.0, 0]),
            "Power Split Ratio": fields.get("Power Split Ratio", [1.0, 0]),
            "Charging C-Rate":   fields.get("Charging C-Rate",   [1.0, 0]),
        }
        fields_si = self.data_entry_widget.get_values_si()
        return data, self.create_rcaide_structure(data, fields_si)

    def load_data_values(self, data):
        if "distributor name" in data:
            self.section_name_edit.setText(data["distributor name"])
        self.data_entry_widget.load_data(data)
        self._loaded_propulsors = list(data.get("assigned_propulsors", []))
        self._loaded_sources    = list(data.get("assigned_sources",    []))

    def create_rcaide_structure(self, data, fields_si=None):
        bus = RCAIDE.Library.Components.Powertrain.Distributors.Electrical_Bus()
        bus.tag = data["distributor name"]
        if fields_si:
            bus.efficiency        = fields_si.get("Efficiency",        [1.0])[0]
            bus.voltage           = fields_si.get("Voltage",           [0.0])[0]
            bus.power_split_ratio = fields_si.get("Power Split Ratio", [1.0])[0]
            bus.charging_c_rate   = fields_si.get("Charging C-Rate",   [1.0])[0]
        return bus
