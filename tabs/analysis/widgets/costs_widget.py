# RCAIDE_GUI/tabs/analysis/widgets/costs_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
from PyQt6.QtWidgets import QLabel
from tabs.analysis.widgets.analysis_data_widget import AnalysisDataWidget
from utilities import create_line_bar

# ------------------------------------------------------------------------------
# Costs Widget
# ------------------------------------------------------------------------------
class CostsWidget(AnalysisDataWidget):
    title = "Costs"

    def __init__(self):
        super().__init__()
        self.main_layout.addWidget(QLabel("Costs analysis is not yet available."))
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, _vehicle):
        return None
