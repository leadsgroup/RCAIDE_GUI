# RCAIDE_GUI/tabs/analysis/widgets/energy_widget.py

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
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

# ------------------------------------------------------------------------------
# Energy Widget
# ------------------------------------------------------------------------------
class EnergyWidget(AnalysisDataWidget):
    def __init__(self):
        super(EnergyWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Energy</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, vehicle: RCAIDE.Vehicle):
        energy = RCAIDE.Framework.Analyses.Energy.Energy() 
        return energy
