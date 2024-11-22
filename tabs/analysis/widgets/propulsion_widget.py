from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE


class PropulsionWidget(AnalysisDataWidget):
    def __init__(self,show_title: bool=False):
        super(PropulsionWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        if show_title:
            self.main_layout.addWidget(QLabel("<b>Propulsion</b>"))
        self.main_layout.addWidget(create_line_bar())

        options = ["Rotor Wake Fidelity 0",
                   "Rotor Wake Fidelity 1", "Rotor Wake Fidelity 2"]
        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems(options)

        self.main_layout.addWidget(self.analysis_selector)
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def create_analysis(self, _vehicle):
        analysis_num = self.analysis_selector.currentIndex()
        if analysis_num == 0:
            propulsion = RCAIDE.Framework.Analyses.Propulsion.Rotor_Wake_Fidelity_Zero()
        elif analysis_num == 1:
            propulsion = RCAIDE.Framework.Analyses.Propulsion.Rotor_Wake_Fidelity_One()
        else:
            propulsion = RCAIDE.Framework.Analyses.Propulsion.Rotor_Wake_Fidelity_Two()

        return propulsion
    
    def get_values(self):
        return {"analysis_num": self.analysis_selector.currentIndex()}
    
    def load_values(self, values):
        super().load_values(values)
        self.analysis_selector.setCurrentIndex(values["analysis_num"])
