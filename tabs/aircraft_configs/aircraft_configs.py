from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, QLabel, QLineEdit

from tabs.geometry.geometry import GeometryWidget
from utilities import Units
from widgets import DataEntryWidget

import values
# import RCAIDE


class AircraftConfigsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.vehicle = None
        self.data = None

        self.data_entry_widget = None

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Vehicle Configurations"])
        tree_layout.addWidget(self.tree)
        
        self.main_layout = QVBoxLayout()
        # update_layout_button = QPushButton("Load Aircraft Geometry")
        # update_layout_button.clicked.connect(self.update_layout)
        # self.main_layout.addWidget(QLabel("hi"))
        # TODO: make this automatic
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Config Name:"), 3)
        name_layout.addWidget(QLineEdit(), 7)
        self.main_layout.addLayout(name_layout)

        self.update_layout()

        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_data)
        self.main_layout.addWidget(save_button)
        
        new_config_button = QPushButton("New Configuration")
        self.main_layout.addWidget(new_config_button)

        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(self.main_layout, 7)
        self.setLayout(base_layout)

    def update_layout(self):
        self.vehicle = values.vehicle
        self.data = values.geometry_data

        control_surface_data = []

        for wing in self.data[2]:
            for control_surface in wing["control_surfaces"]:
                control_surface_data.append(control_surface)

        data_units_labels = []
        for control_surface in control_surface_data:
            data_units_labels.append(
                (control_surface["CS name"] + " Deflection", Units.Angle))
        
        if self.data_entry_widget is not None:
            self.main_layout.removeWidget(self.data_entry_widget)
        
        self.data_entry_widget = DataEntryWidget(data_units_labels)
        self.main_layout.insertWidget(1, self.data_entry_widget)
    
    def new_configuration(self):
        assert self.data_entry_widget is not None
        self.data_entry_widget.clear_values()

    def save_data(self):
        pass


def get_widget() -> QWidget:
    return AircraftConfigsWidget()
