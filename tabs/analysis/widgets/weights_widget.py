from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from utilities import Units, create_line_bar
from widgets import DataEntryWidget


class WeightsWidget(QWidget):
    data_units_labels = [
        ("Max Takeoff Weight", Units.Mass),
        ("Actual Takeoff Weight", Units.Mass),
        ("Operating Empty Weight", Units.Mass),
        ("Maximum Zero Fuel Weight", Units.Mass),
        ("Cargo Weight", Units.Mass),
        ("Ultimate Load", Units.Unitless),
        ("Limit Load", Units.Unitless),
        ("Reference Area", Units.Area),
        ("Passengers", Units.Count),
    ]

    def __init__(self):
        super(WeightsWidget, self).__init__()
        self.data_values = {}
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Weights</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.data_entry_widget = DataEntryWidget(self.data_units_labels)
        self.main_layout.addWidget(self.data_entry_widget)

        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)
