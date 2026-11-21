# RCAIDE_GUI/tabs/geometry/widgets/powertrain/sources/battery_pack_widget.py

# Created: Nov 2026, M. Clarke

import RCAIDE
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                              QPushButton, QComboBox, QFrame, QSizePolicy)

from tabs.geometry.widgets import GeometryDataWidget
from tabs.geometry.widgets.powertrain.sources.battery_module_widget import BatteryModuleWidget
from common_widgets import DataEntryWidget
from utilities import Units, BTN_STYLE
import rcaide_io


class BatteryPackWidget(GeometryDataWidget):
    """Editor widget for a RCAIDE ``Battery_Pack`` source and its battery modules.

    The pack is the energy source wired to electrical buses in the Connections
    matrix.  Its modules are edited with ``BatteryModuleWidget`` entries listed
    under the pack.
    """

    source_type = "Battery Pack"

    def __init__(self, index, on_delete, data_values=None):
        super().__init__()
        self.index = index
        self.on_delete = on_delete
        # RCAIDE pack loaded from a file (stripped JSON dict); None for a new pack
        self.loaded_component = None

        layout = QVBoxLayout()

        # ── Name + delete ──────────────────────────────────────────────────
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Battery Pack Name:"))
        self.section_name_edit = QLineEdit(self)
        name_row.addWidget(self.section_name_edit)
        del_btn = QPushButton("Delete", self)
        del_btn.setStyleSheet(BTN_STYLE)
        del_btn.setMaximumWidth(80)
        del_btn.clicked.connect(self.delete_pressed)
        name_row.addWidget(del_btn)
        layout.addLayout(name_row)

        # ── Module electric configuration ──────────────────────────────────
        config_row = QHBoxLayout()
        config_row.addWidget(QLabel("Module Connection:"))
        self.module_configuration_combo = QComboBox(self)
        self.module_configuration_combo.addItems(["Series", "Parallel"])
        config_row.addWidget(self.module_configuration_combo)
        config_row.addStretch()
        layout.addLayout(config_row)

        # ── Pack fields ────────────────────────────────────────────────────
        self.data_entry_widget = DataEntryWidget([
            ("Charging C-Rate",   Units.Unitless),
            ("Power Split Ratio", Units.Unitless),
        ])
        layout.addWidget(self.data_entry_widget)

        # ── Modules ────────────────────────────────────────────────────────
        self.modules_layout = QVBoxLayout()
        layout.addLayout(self.modules_layout)

        add_btn = QPushButton("Add Battery Module", self)
        add_btn.setStyleSheet(BTN_STYLE)
        add_btn.setMaximumWidth(220)
        add_btn.clicked.connect(lambda: self.add_module())
        layout.addWidget(add_btn)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        if data_values:
            self.load_data_values(data_values)
        else:
            self.data_entry_widget.load_data({"Charging C-Rate": [1.0, 0], "Power Split Ratio": [1.0, 0]})

    # ── Modules ────────────────────────────────────────────────────────────

    def module_widgets(self):
        widgets = []
        for i in range(self.modules_layout.count()):
            widget = self.modules_layout.itemAt(i).widget()
            if isinstance(widget, BatteryModuleWidget):
                widgets.append(widget)
        return widgets

    def add_module(self, data_values=None):
        widget = BatteryModuleWidget(self.modules_layout.count(), self.delete_module, data_values)
        self.modules_layout.addWidget(widget)

    def delete_module(self, index):
        widget = self.modules_layout.itemAt(index).widget()
        self.modules_layout.removeWidget(widget)
        widget.deleteLater()
        for i, module_widget in enumerate(self.module_widgets()):
            module_widget.index = i

    # ── Data API ───────────────────────────────────────────────────────────

    def get_data_values(self):
        fields = self.data_entry_widget.get_values()
        module_data = []
        modules     = []
        for widget in self.module_widgets():
            data_i, module = widget.get_data_values()
            module_data.append(data_i)
            modules.append(module)

        data = {
            "Source Name":          self.section_name_edit.text(),
            "source_type":          "Battery Pack",
            "Module Configuration": self.module_configuration_combo.currentText(),
            "Charging C-Rate":      fields.get("Charging C-Rate",   [1.0, 0]),
            "Power Split Ratio":    fields.get("Power Split Ratio", [1.0, 0]),
            "modules":              module_data,
        }
        if self.loaded_component is not None:
            data["rcaide_component"] = self.loaded_component
        fields_si = self.data_entry_widget.get_values_si()
        return data, self.create_rcaide_structure(data, fields_si, modules)

    def load_data_values(self, data):
        self.loaded_component = data.get("rcaide_component")
        self.section_name_edit.setText(data.get("Source Name", ""))
        idx = self.module_configuration_combo.findText(data.get("Module Configuration", "Series"))
        if idx >= 0:
            self.module_configuration_combo.setCurrentIndex(idx)
        self.data_entry_widget.load_data(data)
        for module_data in data.get("modules", []):
            self.add_module(module_data)

    def create_rcaide_structure(self, data, fields_si, modules):
        # Start from the loaded pack so settings the form does not show are kept; modules come from the module editors
        pack = RCAIDE.Library.Components.Powertrain.Sources.Batteries.Battery_Pack()
        if self.loaded_component is not None:
            pack = rcaide_io.component_from_dict(self.loaded_component)
            pack.modules = RCAIDE.Framework.Core.Container()
        pack.tag                                   = data["Source Name"]
        pack.battery_module_electric_configuration = data["Module Configuration"]
        pack.charging_c_rate                       = fields_si.get("Charging C-Rate",   [1.0])[0]
        pack.power_split_ratio                     = fields_si.get("Power Split Ratio", [1.0])[0]
        for module in modules:
            pack.append_module(module)
        return pack

    def delete_pressed(self):
        if self.on_delete:
            self.on_delete(self.index)
