# RCAIDE_GUI/tabs/geometry/widgets/powertrain/distributors/coolant_line_widget.py

# Created: Jun 2026, M. Clarke

import RCAIDE
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSizePolicy

from tabs.geometry.widgets.powertrain.distributors.base_distributor_widget import BaseDistributorWidget
from utilities import BTN_STYLE


class CoolantLineWidget(BaseDistributorWidget):
    distributor_type = "Coolant Line"

    def __init__(self, index, on_delete, data_values=None):
        super().__init__(index, on_delete)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.addWidget(QLabel("Coolant Line Name:"))
        self.section_name_edit = QLineEdit(self)
        row.addWidget(self.section_name_edit)
        del_btn = QPushButton("Delete", self)
        del_btn.setStyleSheet(BTN_STYLE)
        del_btn.setMaximumWidth(80)
        del_btn.clicked.connect(self.delete_button_pressed)
        row.addWidget(del_btn)
        layout.addLayout(row)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        if data_values:
            self.load_data_values(data_values)

    def get_data_values(self):
        data = {
            "distributor name": self.section_name_edit.text(),
            "distributor_type": "Coolant Line",
        }
        return data, self.create_rcaide_structure(data)

    def load_data_values(self, data):
        if "distributor name" in data:
            self.section_name_edit.setText(data["distributor name"])
        self._loaded_propulsors = list(data.get("assigned_propulsors", []))
        self._loaded_sources    = list(data.get("assigned_sources",    []))

    def create_rcaide_structure(self, data):
        line = RCAIDE.Library.Components.Powertrain.Distributors.Coolant_Line()
        line.tag = data["distributor name"]
        return line
