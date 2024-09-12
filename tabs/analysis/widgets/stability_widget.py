from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE


class StabilityWidget(AnalysisDataWidget):
    def __init__(self):
        super(StabilityWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Stability</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(QLabel("VLM Perturbation Method"))
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, vehicle):
        stability = RCAIDE.Framework.Analyses.Stability.Vortex_Lattice_Method()
        stability.geometry = vehicle
        return stability
