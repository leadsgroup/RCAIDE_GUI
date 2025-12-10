from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QComboBox


from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget
from utilities import Units
from widgets import DataEntryWidget
import os
import sys

import RCAIDE


class WeightsWidget(AnalysisDataWidget):
    def __init__(self):
        super(WeightsWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Weights</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.weight_options = [
            # "No selection",
            "Conventional",
            "Conventional BWB",
            "Conventional General Aviation",
            "Conventional_Transport",
            "Electric",
            "Electric_General_Aviation",
            "Electric_VTOL",
            "Hybrid",
            "Hydrogen",
            "Hydrogen_Transport"
        ]
        weight_selector_layout = QHBoxLayout()
        weight_selector_layout.addWidget(QLabel("Weight Selection Option:"))
        self.weight_selection = QComboBox()
        self.weight_selection.addItems(self.weight_options)
        self.weight_selection.currentIndexChanged.connect(self.on_weights_changed)
        weight_selector_layout.addWidget(self.weight_selection)
        weight_selector_layout.addStretch()
        self.main_layout.addLayout(weight_selector_layout)

        self.dynamic_weight_container = QWidget()
        self.dynamic_weight_layout = QVBoxLayout(self.dynamic_weight_container)
        self.dynamic_weight_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.dynamic_weight_container)

        self.main_layout.addStretch()
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def on_weights_changed(self, index):
        self.clear_dynamic_weights_layout()
        selected_option = self.weight_selection.currentText()
        if selected_option == "Conventional":
            self.add_conventional_fields()

    def add_conventional_fields(self):
        conventional_data_units_labels = [
            ("Update Center of Gravity", Units.Boolean),
            ("Update Moment of Inertia", Units.Boolean),
            ("Weight Correction: Structural Paint", Units.Count),
            ("Weight Correction: Operational Items ETOPS", Units.Count),
            ("Update Mass Properties", Units.Boolean),
            ("FLOPS Fidelity", Units.Unitless)
        ]
        conventional_widget = DataEntryWidget(conventional_data_units_labels)
        self.dynamic_weight_layout.addWidget(conventional_widget)

    def clear_dynamic_weights_layout(self):
        if self.dynamic_weight_layout is not None:
            while self.dynamic_weight_layout.count():
                item = self.dynamic_weight_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def create_analysis(self, vehicle: RCAIDE.Vehicle):
        selected_option = self.weight_selection.currentText()
        # if selected_option == "No selection":
        #     return None
        weights = RCAIDE.Framework.Analyses.Weights.Conventional() 
        return weights
