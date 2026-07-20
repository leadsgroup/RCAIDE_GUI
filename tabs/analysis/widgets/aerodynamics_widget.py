# RCAIDE_GUI/tabs/analysis/widgets/aerodynamics_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE

from tabs.analysis.widgets.analysis_data_widget import AnalysisDataWidget
from utilities import create_line_bar, Units, set_data
from common_widgets import DataEntryWidget

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QComboBox

# ------------------------------------------------------------------------------
# Aerodynamics Widget
# ------------------------------------------------------------------------------
class AerodynamicsWidget(AnalysisDataWidget):
    title = "Aerodynamics"

    _ANALYSES = ["Vortex Lattice Method"]

    # Curated VLM settings: (display label, units, RCAIDE settings attribute)
    _SETTINGS_FIELDS = [[
        ("Use Surrogate",               Units.Boolean,  "use_surrogate"),
        ("Reuse Training Data",         Units.Boolean,  "reuse_training_data"),
        ("Spanwise Vortices",           Units.Count,    "number_of_spanwise_vortices"),
        ("Chordwise Vortices",          Units.Count,    "number_of_chordwise_vortices"),
        ("Spanwise Cosine Spacing",     Units.Boolean,  "spanwise_cosine_spacing"),
        ("Model Fuselage",              Units.Boolean,  "model_fuselage"),
        ("Fuselage Spanwise Vortices",  Units.Count,    "number_of_fuselage_spanwise_vortices"),
        ("Fuselage Chordwise Vortices", Units.Count,    "number_of_fuselage_chordwise_vortices"),
        ("Propeller Wake Model",        Units.Boolean,  "propeller_wake_model"),
        ("Fuselage Lift Correction",    Units.Unitless, "fuselage_lift_correction"),
        ("Trim Drag Correction Factor", Units.Unitless, "trim_drag_correction_factor"),
    ]]

    # Defaults mirror RCAIDE __defaults__ values
    _defaults = [{
        "Use Surrogate":               [True,  0],
        "Reuse Training Data":         [False, 0],
        "Spanwise Vortices":           [30,    0],
        "Chordwise Vortices":          [15,    0],
        "Spanwise Cosine Spacing":     [True,  0],
        "Model Fuselage":              [False, 0],
        "Fuselage Spanwise Vortices":  [4,     0],
        "Fuselage Chordwise Vortices": [10,    0],
        "Propeller Wake Model":        [False, 0],
        "Fuselage Lift Correction":    [1.20,  0],
        "Trim Drag Correction Factor": [1.02,  0],
    }]

    def __init__(self):
        super().__init__()

        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems(self._ANALYSES)
        self.analysis_selector.currentIndexChanged.connect(self.on_analysis_change)
        self.main_layout.addWidget(self.analysis_selector)

        self.data_entry_widget = DataEntryWidget(
            [(lbl, units) for lbl, units, _ in self._SETTINGS_FIELDS[0]], num_cols=1
        )
        self.data_entry_widget.load_data(self._defaults[0])
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def on_analysis_change(self, index):
        self.main_layout.removeWidget(self.data_entry_widget)
        self.data_entry_widget.deleteLater()
        self.data_entry_widget = DataEntryWidget(
            [(lbl, units) for lbl, units, _ in self._SETTINGS_FIELDS[index]], num_cols=1
        )
        self.data_entry_widget.load_data(self._defaults[index])
        self.main_layout.insertWidget(self.main_layout.count() - 1, self.data_entry_widget)

    def create_scroll_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        self.main_layout = QVBoxLayout(scroll_content)
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout_scroll)

    def create_analysis(self, vehicle: RCAIDE.Vehicle):
        index = self.analysis_selector.currentIndex()
        aerodynamics = RCAIDE.Framework.Analyses.Aerodynamics.Vortex_Lattice_Method()
        values = self.data_entry_widget.get_values_si()
        for label, _units, rcaide_attr in self._SETTINGS_FIELDS[index]:
            if label in values and values[label] is not None:
                set_data(aerodynamics.settings, rcaide_attr, values[label][0])
        return aerodynamics

    def get_values(self):
        return self.data_entry_widget.get_values()

    def load_values(self, values):
        super().load_values(values)
        self.data_entry_widget.load_data(values)
