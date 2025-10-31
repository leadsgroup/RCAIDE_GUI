from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE


class CostsWidget(AnalysisDataWidget):
    def __init__(self):
        super(CostsWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Costs</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(
            QLabel("Computes industrial and operating costs"))
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, vehicle):
        costs = RCAIDE.Framework.Analyses.Costs.Costs()
        costs.vehicle = vehicle
        return costs
