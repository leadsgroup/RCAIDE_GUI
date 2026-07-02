# RCAIDE_GUI/tabs/analysis/widgets/weights_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE

from tabs.analysis.widgets.analysis_data_widget import AnalysisDataWidget
from utilities import create_line_bar, Units, set_data
from common_widgets import DataEntryWidget

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox

# ------------------------------------------------------------------------------
# Weights Widget
# ------------------------------------------------------------------------------
class WeightsWidget(AnalysisDataWidget):
    title = "Weights"

    _CLASS_MAP = {
        "Conventional Transport":        RCAIDE.Framework.Analyses.Weights.Conventional_Transport,
        "Conventional BWB":              RCAIDE.Framework.Analyses.Weights.Conventional_BWB,
        "Conventional General Aviation": RCAIDE.Framework.Analyses.Weights.Conventional_General_Aviation,
        "Electric Transport":            RCAIDE.Framework.Analyses.Weights.Electric_Transport,
        "Electric General Aviation":     RCAIDE.Framework.Analyses.Weights.Electric_General_Aviation,
        "Electric VTOL":                 RCAIDE.Framework.Analyses.Weights.Electric_VTOL,
        "Hybrid":                        RCAIDE.Framework.Analyses.Weights.Hybrid,
        "Cryogenic Transport":           RCAIDE.Framework.Analyses.Weights.Cryogenic_Transport,
        "Cryogenic BWB":                 RCAIDE.Framework.Analyses.Weights.Cryogenic_BWB,
    }

    _SETTINGS_FIELDS = [
        ("Run Weights Analysis",    Units.Boolean, "run_weights_analysis"),
        ("Overwrite OEW",           Units.Boolean, "overwrite_operating_empty_weight"),
        ("Run CG Analysis",         Units.Boolean, "run_center_of_gravity_analysis"),
        ("Run MOI Analysis",        Units.Boolean, "run_moments_of_inertia_analysis"),
        ("Write Mass Properties",   Units.Boolean, "write_mass_properties"),
        ("Iterate MTOW",            Units.Boolean, "iterate_mtow"),
    ]

    _defaults = {
        "Run Weights Analysis":  [True,  0],
        "Overwrite OEW":         [True,  0],
        "Run CG Analysis":       [False, 0],
        "Run MOI Analysis":      [False, 0],
        "Write Mass Properties": [False, 0],
        "Iterate MTOW":          [False, 0],
    }

    def __init__(self):
        super().__init__()

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Weight Method:"))
        self.weight_selection = QComboBox()
        self.weight_selection.addItems(list(self._CLASS_MAP.keys()))
        selector_row.addWidget(self.weight_selection)
        selector_row.addStretch()
        self.main_layout.addLayout(selector_row)

        self.data_entry_widget = DataEntryWidget(
            [(lbl, units) for lbl, units, _ in self._SETTINGS_FIELDS]
        )
        self.data_entry_widget.load_data(self._defaults)
        self.main_layout.addWidget(self.data_entry_widget)

        self.main_layout.addStretch()
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, _vehicle):
        cls = self._CLASS_MAP.get(self.weight_selection.currentText())
        if cls is None:
            return None
        weights = cls()
        values = self.data_entry_widget.get_values()
        for label, _units, rcaide_attr in self._SETTINGS_FIELDS:
            if label in values and values[label] is not None:
                set_data(weights.settings, rcaide_attr, values[label][0])
        return weights

    def get_values(self):
        data = self.data_entry_widget.get_values()
        data["weight_method"] = self.weight_selection.currentText()
        return data

    def load_values(self, values):
        super().load_values(values)
        method = values.get("weight_method", "Conventional Transport")
        if method in self._CLASS_MAP:
            self.weight_selection.setCurrentText(method)
        self.data_entry_widget.load_data(values)
