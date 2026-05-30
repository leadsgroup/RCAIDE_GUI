# RCAIDE_GUI/tabs/analysis/widgets/costs_widget.py

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
# Costs Widget
# ------------------------------------------------------------------------------
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
        return costs
