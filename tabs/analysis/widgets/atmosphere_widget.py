from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE


class AtmosphereWidget(QWidget, AnalysisDataWidget):
    def __init__(self):
        super(AtmosphereWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Atmosphere</b>"))
        self.main_layout.addWidget(create_line_bar())

        options = ["1976 US Standard Atmosphere", "Constant Temperature"]
        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems(options)

        self.main_layout.addWidget(self.analysis_selector)
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self):
        analysis_num = self.analysis_selector.currentIndex()
        if analysis_num == 0:
            return RCAIDE.Framework.Analyses.Atmospheric.US_Standard_1976()
        else:
            return RCAIDE.Framework.Analyses.Atmospheric.Constant_Temperature()
