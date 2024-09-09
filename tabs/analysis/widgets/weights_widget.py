from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE


class WeightsWidget(QWidget, AnalysisDataWidget):
    def __init__(self):
        super(WeightsWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Weights</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, vehicle: RCAIDE.Vehicle):
        weights = RCAIDE.Framework.Analyses.Weights.Weights_Transport()
        weights.vehicle = vehicle
        return weights
