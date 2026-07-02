# RCAIDE_GUI/tabs/analysis/widgets/propulsion_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
from PyQt6.QtWidgets import QLabel
from tabs.analysis.widgets.analysis_data_widget import AnalysisDataWidget
from utilities import create_line_bar

# ------------------------------------------------------------------------------
# Propulsion Widget
# ------------------------------------------------------------------------------
class PropulsionWidget(AnalysisDataWidget):
    title = "Propulsion"

    def __init__(self):
        super().__init__()
        self.main_layout.addWidget(QLabel("Propulsion analysis is not yet available."))
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, _vehicle):
        return None
