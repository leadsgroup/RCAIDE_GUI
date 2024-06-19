from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisWidget

import RCAIDE


class PlanetsWidget(QWidget, AnalysisWidget):
    def __init__(self):
        super(PlanetsWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Planets</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(QLabel("Earth"))
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self):
        planet = RCAIDE.Framework.Analyses.Planets.Planet()

        return planet
