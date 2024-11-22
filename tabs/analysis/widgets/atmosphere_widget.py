from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE


class AtmosphereWidget(AnalysisDataWidget):
    def __init__(self,show_title: bool=False):
        super(AtmosphereWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        if show_title:
            self.main_layout.addWidget(QLabel("<b>Atmosphere</b>"))

        self.main_layout.addWidget(create_line_bar())

        options = ["1976 US Standard Atmosphere", "Constant Temperature"]
        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems(options)

        self.main_layout.addWidget(self.analysis_selector)
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, _vehicle):
        analysis_num = self.analysis_selector.currentIndex()
        if analysis_num == 0:
            atmosphere = RCAIDE.Framework.Analyses.Atmospheric.US_Standard_1976()
        else:
            atmosphere = RCAIDE.Framework.Analyses.Atmospheric.Constant_Temperature()

        atmosphere.features.planet = RCAIDE.Framework.Analyses.Planets.Planet().features
        return atmosphere
    
    def get_values(self):
        return {"analysis_num": self.analysis_selector.currentIndex()}
    
    def load_values(self, values):
        super().load_values(values)
        self.analysis_selector.setCurrentIndex(values["analysis_num"])