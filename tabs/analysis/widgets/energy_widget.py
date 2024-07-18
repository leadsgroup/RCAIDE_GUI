from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE


class EnergyWidget(QWidget, AnalysisDataWidget):
    def __init__(self):
        super(EnergyWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Energy</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self):
        return RCAIDE.Framework.Analyses.Energy.Energy()
