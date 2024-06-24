from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget

from tabs.geometry.geometry import GeometryWidget
from utilities import Units
from widgets import DataEntryWidget

import RCAIDE


class AircraftConfigsWidget(QWidget):
    def __init__(self, geometry_widget):
        super().__init__()
        self.geometry_widget: GeometryWidget = geometry_widget
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
        update_layout_button = QPushButton("Update Vehicle Data")
        update_layout_button.clicked.connect(self.update_layout)
        self.main_layout.addWidget(update_layout_button)

        self.update_layout()

        save_button = QPushButton("Save Data")
        save_button.clicked.connect(self.save_data)
        self.main_layout.addWidget(save_button)

        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(self.main_layout, 7)
        self.setLayout(base_layout)

    def update_layout(self):
        self.vehicle = self.geometry_widget.get_vehicle()
        self.data = self.geometry_widget.get_data()

        control_surface_data = []

        for wing in self.data[1]:
            for control_surface in wing["control_surfaces"]:
                control_surface_data.append(control_surface)

        data_units_labels = []
        for control_surface in control_surface_data:
            data_units_labels.append(
                (control_surface["CS name"] + " Deflection", Units.Angle))

        self.main_layout.removeWidget(self.data_entry_widget)
        self.data_entry_widget = DataEntryWidget(data_units_labels)
        self.main_layout.insertWidget(1, self.data_entry_widget)

    def save_data(self):
        pass


def get_widget(geometry_widget) -> QWidget:
    return AircraftConfigsWidget(geometry_widget)
