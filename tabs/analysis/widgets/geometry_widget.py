from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QComboBox

from utilities import create_line_bar
from tabs.analysis.widgets import AnalysisDataWidget
from utilities import Units
from widgets import DataEntryWidget
import os
import sys
import RCAIDE


class GeometryWidget(AnalysisDataWidget):
    def __init__(self):
        super(GeometryWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Geometry</b>"))
        self.main_layout.addWidget(create_line_bar())
        

        self.geometry_options = [
            ("Overwrite Reference", Units.Boolean),
            ("Update Fuel Volume", Units.Boolean)
        ]

        self.data_entry_widget  = DataEntryWidget(self.geometry_options)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addStretch()
        self.setLayout(self.main_layout)


    def create_analysis(self, vehicle: RCAIDE.Vehicle):
        geometry = RCAIDE.Framework.Analyses.Geometry.Geometry() 
        data = self.data_entry_widget.get_values()
        if ("Overwrite Reference" in data and
            data["Overwrite Reference"] is not None):
            geometry.settings.overwrite_reference = data["Overwrite Reference"][0]
        if ("Update Fuel Volume" in data and
            data["Update Fuel Volume"] is not None):
            geometry.settings.update_fuel_volume = data["Update Fuel Volume"][0]
        return geometry
