# RCAIDE_GUI/tabs/geometry/widgets/powertrain/sources/battery_module_widget.py

# Created: Jun 2026, M. Clarke

import RCAIDE
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                              QPushButton, QComboBox, QFrame)

from tabs.geometry.widgets import GeometryDataWidget
from common_widgets import DataEntryWidget
from utilities import Units, BTN_STYLE

# Map display name → RCAIDE battery class
_BATTERY_CLASS_MAP = {
    "Lithium Ion NMC":   RCAIDE.Library.Components.Powertrain.Sources.Battery_Modules.Lithium_Ion_NMC,
    "Lithium Ion LFP":   RCAIDE.Library.Components.Powertrain.Sources.Battery_Modules.Lithium_Ion_LFP,
    "Lithium Sulfur":    RCAIDE.Library.Components.Powertrain.Sources.Battery_Modules.Lithium_Sulfur,
    "Aluminum Air":      RCAIDE.Library.Components.Powertrain.Sources.Battery_Modules.Aluminum_Air,
    "Lithium Air":       RCAIDE.Library.Components.Powertrain.Sources.Battery_Modules.Lithium_Air,
    "Generic":           RCAIDE.Library.Components.Powertrain.Sources.Battery_Modules.Generic_Battery_Module,
}

# Map RCAIDE __type__ suffix → display name (for JSON loading)
_BATTERY_TYPE_LABEL = {
    "Lithium_Ion_NMC":           "Lithium Ion NMC",
    "Lithium_Ion_LFP":           "Lithium Ion LFP",
    "Lithium_Sulfur":            "Lithium Sulfur",
    "Aluminum_Air":              "Aluminum Air",
    "Lithium_Air":               "Lithium Air",
    "Generic_Battery_Module":    "Generic",
}


class BatteryModuleWidget(GeometryDataWidget):
    """Editor widget for any RCAIDE battery-module source.

    A chemistry dropdown selects the RCAIDE class to instantiate
    (``Lithium_Ion_NMC``, ``Lithium_Ion_LFP``, ``Lithium_Sulfur``,
    ``Aluminum_Air``, ``Lithium_Air``, or ``Generic_Battery_Module``).
    The remaining fields cover capacity, physical dimensions, and the
    electrical/geometric cell configuration.

    Both ``get_data_values()`` and ``load_data_values()`` use
    ``"Source Name"`` as the primary tag key so that ``_refresh_connections``
    in ``PowertrainWidget`` treats battery modules and fuel tanks uniformly.
    """

    source_type = "Battery Module"

    def __init__(self, index, on_delete, data_values=None):
        super().__init__()
        self.index = index
        self.on_delete = on_delete

        layout = QVBoxLayout()

        # ── Name + delete ──────────────────────────────────────────────────
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Battery Module Name:"))
        self.section_name_edit = QLineEdit(self)
        name_row.addWidget(self.section_name_edit)
        del_btn = QPushButton("Delete", self)
        del_btn.setStyleSheet(BTN_STYLE)
        del_btn.setMaximumWidth(80)
        del_btn.clicked.connect(self._delete_pressed)
        name_row.addWidget(del_btn)
        layout.addLayout(name_row)

        # ── Chemistry selector ─────────────────────────────────────────────
        chem_row = QHBoxLayout()
        chem_row.addWidget(QLabel("Chemistry:"))
        self.chemistry_combo = QComboBox(self)
        self.chemistry_combo.addItems(sorted(_BATTERY_CLASS_MAP.keys()))
        self.chemistry_combo.setCurrentText("Lithium Ion NMC")
        chem_row.addWidget(self.chemistry_combo)
        chem_row.addStretch()
        layout.addLayout(chem_row)

        # ── Module fields ──────────────────────────────────────────────────
        self.data_entry_widget = DataEntryWidget([
            ("Capacity",           Units.Energy),
            ("Length",             Units.Length),
            ("Width",              Units.Length),
            ("Height",             Units.Length),
            ("Series Cells",       Units.Unitless),
            ("Parallel Cells",     Units.Unitless),
            ("Normal Cell Count",  Units.Unitless),
            ("Parallel Cell Count",Units.Unitless),
            ("Stacking Rows",      Units.Unitless),
        ])
        layout.addWidget(self.data_entry_widget)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        self.setLayout(layout)

        if data_values:
            self.load_data_values(data_values)

    # ── Data API ───────────────────────────────────────────────────────────

    def get_data_values(self):
        fields = self.data_entry_widget.get_values()
        data = {
            "Source Name":         self.section_name_edit.text(),
            "source_type":         "Battery Module",
            "Chemistry":           self.chemistry_combo.currentText(),
            "Capacity":            fields.get("Capacity",            [0.0, 0]),
            "Length":              fields.get("Length",              [0.0, 0]),
            "Width":               fields.get("Width",               [0.0, 0]),
            "Height":              fields.get("Height",              [0.0, 0]),
            "Series Cells":        fields.get("Series Cells",        [1,   0]),
            "Parallel Cells":      fields.get("Parallel Cells",      [1,   0]),
            "Normal Cell Count":   fields.get("Normal Cell Count",   [1,   0]),
            "Parallel Cell Count": fields.get("Parallel Cell Count", [1,   0]),
            "Stacking Rows":       fields.get("Stacking Rows",       [3,   0]),
        }
        fields_si = self.data_entry_widget.get_values_si()
        return data, self.create_rcaide_structure(data, fields_si)

    def load_data_values(self, data):
        if "Source Name" in data:
            self.section_name_edit.setText(data["Source Name"])
        chemistry = data.get("Chemistry", "Lithium Ion NMC")
        idx = self.chemistry_combo.findText(chemistry)
        if idx >= 0:
            self.chemistry_combo.setCurrentIndex(idx)
        self.data_entry_widget.load_data(data)

    def create_rcaide_structure(self, data, fields_si=None):
        chemistry = data.get("Chemistry", "Lithium Ion NMC")
        cls = _BATTERY_CLASS_MAP.get(chemistry,
              RCAIDE.Library.Components.Powertrain.Sources.Battery_Modules.Generic_Battery_Module)
        module = cls()
        module.tag = data["Source Name"]
        if fields_si:
            module.capacity = fields_si.get("Capacity", [0.0])[0]
            module.length   = fields_si.get("Length",   [0.0])[0]
            module.width    = fields_si.get("Width",    [0.0])[0]
            module.height   = fields_si.get("Height",   [0.0])[0]
            module.electrical_configuration.series   = int(fields_si.get("Series Cells",   [1])[0])
            module.electrical_configuration.parallel = int(fields_si.get("Parallel Cells", [1])[0])
            module.geometric_configuration.normal_count   = int(fields_si.get("Normal Cell Count",   [1])[0])
            module.geometric_configuration.parallel_count = int(fields_si.get("Parallel Cell Count", [1])[0])
            module.geometric_configuration.stacking_rows  = int(fields_si.get("Stacking Rows",       [3])[0])
        return module

    def _delete_pressed(self):
        if self.on_delete:
            self.on_delete(self.index)
