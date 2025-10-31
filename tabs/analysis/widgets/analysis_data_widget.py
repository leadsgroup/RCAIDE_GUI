from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

import RCAIDE


class AnalysisDataWidget(QWidget):
    def __init__(self):
        super(AnalysisDataWidget, self).__init__()
        self.setVisible(True)
    
    def create_analysis(self, vehicle: RCAIDE.Vehicle):
        return RCAIDE.Framework.Analyses.Analysis()
    
    def get_values(self):
        return {}
    
    def load_values(self, values):
        self.setVisible(values["enabled"])
