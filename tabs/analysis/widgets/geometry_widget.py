# RCAIDE_GUI/tabs/analysis/widgets/geometry_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE

from tabs.analysis.widgets.analysis_data_widget import AnalysisDataWidget
from utilities import create_line_bar, Units, set_data
from common_widgets import DataEntryWidget

# ------------------------------------------------------------------------------
# Geometry Widget
# ------------------------------------------------------------------------------
class GeometryWidget(AnalysisDataWidget):
    title = "Geometry"

    _SETTINGS_FIELDS = [
        ("Overwrite Reference",      Units.Boolean, "overwrite_reference"),
        ("Compute Fuel Volume",      Units.Boolean, "compute_fuel_volume"),
        ("Update Max Fuel",          Units.Boolean, "update_max_fuel"),
        ("Unique Geometry",          Units.Boolean, "unique_geometry"),
        ("Write Geometry Properties",Units.Boolean, "write_geometry_properties"),
    ]

    _defaults = {
        "Overwrite Reference":       [True,  0],
        "Compute Fuel Volume":       [True,  0],
        "Update Max Fuel":           [False, 0],
        "Unique Geometry":           [False, 0],
        "Write Geometry Properties": [False, 0],
    }

    def __init__(self):
        super().__init__()

        self.data_entry_widget = DataEntryWidget(
            [(lbl, units) for lbl, units, _ in self._SETTINGS_FIELDS]
        )
        self.data_entry_widget.load_data(self._defaults)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addStretch()
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, _vehicle):
        geometry = RCAIDE.Framework.Analyses.Geometry.Geometry()
        values = self.data_entry_widget.get_values()
        for label, _units, rcaide_attr in self._SETTINGS_FIELDS:
            if label in values and values[label] is not None:
                set_data(geometry.settings, rcaide_attr, values[label][0])
        return geometry

    def get_values(self):
        return self.data_entry_widget.get_values()

    def load_values(self, values):
        super().load_values(values)
        self.data_entry_widget.load_data(values)
