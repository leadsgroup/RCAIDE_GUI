from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisWidget

import RCAIDE


class PropulsionWidget(QWidget, AnalysisWidget):
    def __init__(self):
        super(PropulsionWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Propulsion</b>"))
        self.main_layout.addWidget(create_line_bar())

        options = ["Rotor Wake Fidelity 0",
                   "Rotor Wake Fidelity 1", "Rotor Wake Fidelity 2"]
        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems(options)

        self.main_layout.addWidget(self.analysis_selector)
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self):
        analysis_num = self.analysis_selector.currentIndex()
        if analysis_num == 0:
            propulsion = RCAIDE.Framework.Analyses.Propulsion.Rotor_Wake_Fidelity_Zero()
        elif analysis_num == 1:
            propulsion = RCAIDE.Framework.Analyses.Propulsion.Rotor_Wake_Fidelity_One()
        else:
            propulsion = RCAIDE.Framework.Analyses.Propulsion.Rotor_Wake_Fidelity_Two()

        return propulsion
