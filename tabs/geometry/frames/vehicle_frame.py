import RCAIDE
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QScrollArea

from tabs.geometry.frames import GeometryFrame
from utilities import show_popup, create_line_bar, Units
from widgets import DataEntryWidget


class VehicleFrame(QWidget, GeometryFrame):
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
        super().__init__()
        self.data = []
        self.data_entry_widget = None
        self.main_layout = QVBoxLayout()
        self.create_scroll_area()
        
        self.main_layout.addWidget(QLabel("<b>Vehicle</b>"))
        self.main_layout.addWidget(create_line_bar())
        
        self.name_layout = QHBoxLayout()
        self.name_layout.addWidget(QLabel("Name:"), 3)
        self.name_line_edit = QLineEdit()
        self.name_layout.addWidget(self.name_line_edit, 7)
        
        self.main_layout.addLayout(self.name_layout)
        
        self.data_entry_widget = DataEntryWidget(self.data_units_labels)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))
