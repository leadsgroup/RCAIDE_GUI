# RCAIDE_GUI/tabs/analysis/widgets/planets_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
# RCAIDE imports
import RCAIDE

# RCAIDE-GUI imports
from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

# PyQt imports
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

# ------------------------------------------------------------------------------
# Planets Widget
# ------------------------------------------------------------------------------
class PlanetsWidget(AnalysisDataWidget):
    def __init__(self):
        super(PlanetsWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Planets</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(QLabel("Earth"))
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, _vehicle):
        planet = RCAIDE.Framework.Analyses.Planets.Earth()
        return planet
