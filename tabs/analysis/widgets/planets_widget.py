from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE


class PlanetsWidget(AnalysisDataWidget):
    def __init__(self,show_title: bool=False):
        super(PlanetsWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        if show_title:
            self.main_layout.addWidget(QLabel("<b>Planets</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(QLabel("Earth"))
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, _vehicle):
        planet = RCAIDE.Framework.Analyses.Planets.Earth()
        return planet
