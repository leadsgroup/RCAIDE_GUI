# RCAIDE_GUI/tabs/analysis/widgets/stability_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE

from tabs.analysis.widgets.analysis_data_widget import AnalysisDataWidget
from utilities import create_line_bar, Units, set_data
from common_widgets import DataEntryWidget

# ------------------------------------------------------------------------------
# Stability Widget
# ------------------------------------------------------------------------------
class StabilityWidget(AnalysisDataWidget):
    title = "Stability"

    # Curated VLM settings: (display label, units, RCAIDE settings attribute)
    _SETTINGS_FIELDS = [
        ("Use Surrogate",               Units.Boolean, "use_surrogate"),
        ("Spanwise Vortices",           Units.Count,   "number_of_spanwise_vortices"),
        ("Chordwise Vortices",          Units.Count,   "number_of_chordwise_vortices"),
        ("Spanwise Cosine Spacing",     Units.Boolean, "spanwise_cosine_spacing"),
        ("Model Fuselage",              Units.Boolean, "model_fuselage"),
        ("Fuselage Spanwise Vortices",  Units.Count,   "number_of_fuselage_spanwise_vortices"),
        ("Fuselage Chordwise Vortices", Units.Count,   "number_of_fuselage_chordwise_vortices"),
        ("Propeller Wake Model",        Units.Boolean, "propeller_wake_model"),
    ]

    _defaults = {
        "Use Surrogate":               [True,  0],
        "Spanwise Vortices":           [30,    0],
        "Chordwise Vortices":          [15,    0],
        "Spanwise Cosine Spacing":     [True,  0],
        "Model Fuselage":              [True,  0],
        "Fuselage Spanwise Vortices":  [4,     0],
        "Fuselage Chordwise Vortices": [10,    0],
        "Propeller Wake Model":        [False, 0],
    }

    def __init__(self):
        super().__init__()

        self.data_entry_widget = DataEntryWidget(
            [(lbl, units) for lbl, units, _ in self._SETTINGS_FIELDS], num_cols=1
        )
        self.data_entry_widget.load_data(self._defaults)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, _vehicle):
        stability = RCAIDE.Framework.Analyses.Stability.Vortex_Lattice_Method()
        values = self.data_entry_widget.get_values_si()
        for label, _units, rcaide_attr in self._SETTINGS_FIELDS:
            if label in values and values[label] is not None:
                set_data(stability.settings, rcaide_attr, values[label][0])
        return stability

    def get_values(self):
        return self.data_entry_widget.get_values()

    def load_values(self, values):
        super().load_values(values)
        self.data_entry_widget.load_data(values)
