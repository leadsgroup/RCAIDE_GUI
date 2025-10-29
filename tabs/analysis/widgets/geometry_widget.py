from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE


class GeometryWidget(AnalysisDataWidget):
    def __init__(self):
        super(GeometryWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Geometry</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, vehicle: RCAIDE.Vehicle):
        geometry = RCAIDE.Framework.Analyses.Geometry.Geometry()
        geometry.vehicle = vehicle
        return geometry
