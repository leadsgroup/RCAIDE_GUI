from PyQt6.QtCore import QLine
from PyQt6.QtWidgets import QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, QLabel, QLineEdit

from tabs.geometry.geometry import GeometryWidget
from utilities import Units, create_line_bar
from widgets import DataEntryWidget

import values
# import RCAIDE


class AircraftConfigsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.vehicle = None
        self.data = None
        self.index = -1

        self.cs_de_widget = None
        self.prop_de_widget = None

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Vehicle Configurations"])
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        tree_layout.addWidget(self.tree)

        self.main_layout = QVBoxLayout()
        self.name_line_edit = QLineEdit()
        name_layout = QHBoxLayout()

        name_layout.addWidget(QLabel("Config Name:"), 3)
        name_layout.addWidget(self.name_line_edit, 7)
        self.main_layout.addLayout(name_layout)

        self.main_layout.addWidget(QLabel("<b>Control Surfaces</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.main_layout.addWidget(QLabel("<b>Propulsors</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.update_layout()

        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_data)
        self.main_layout.addWidget(save_button)

        new_config_button = QPushButton("New Configuration")
        new_config_button.clicked.connect(self.new_configuration)
        self.main_layout.addWidget(new_config_button)

        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(self.main_layout, 7)
        self.setLayout(base_layout)

    def update_layout(self):
        self.vehicle = values.vehicle
        self.data = values.geometry_data

        control_surface_data = []
        propulsor_data = []

        for wing in self.data[2]:
            for control_surface in wing["control_surfaces"]:
                control_surface_data.append(control_surface)

        for energy_network in self.data[5]:
            for fuel_line in energy_network["energy_network"]:
                for propulsor in fuel_line["propulsor data"]:
                    propulsor_data.append(propulsor)

        cs_deflections_labels = []
        propulsor_labels = []
        for control_surface in control_surface_data:
            cs_deflections_labels.append(
                (control_surface["CS name"] + " Deflection", Units.Angle)
            )

        for propulsor in propulsor_data:
            propulsor_labels.append(
                (propulsor["propulsor name"] + " Enabled", Units.Boolean)
            )

        if self.cs_de_widget is not None:
            self.main_layout.removeWidget(self.cs_de_widget)
            self.main_layout.removeWidget(self.prop_de_widget)

        self.cs_de_widget = DataEntryWidget(cs_deflections_labels)
        self.main_layout.insertWidget(3, self.cs_de_widget)

        self.prop_de_widget = DataEntryWidget(propulsor_labels)
        self.main_layout.insertWidget(6, self.prop_de_widget)

    def new_configuration(self):
        assert self.cs_de_widget is not None
        self.cs_de_widget.clear_values()

        assert self.prop_de_widget is not None
        self.cs_de_widget.clear_values()
        
        self.index = -1

    def get_data(self):
        data = {}
        data["config name"] = self.name_line_edit.text()

        assert self.cs_de_widget is not None and self.prop_de_widget is not None
        data["cs deflections"] = self.cs_de_widget.get_values()
        data["propulsors"] = self.prop_de_widget.get_values()

        return data

    def save_data(self):
        data = self.get_data()
        if self.index == -1:
            self.index = len(values.aircraft_configs)
            values.aircraft_configs.append(data)
            tree_item = QTreeWidgetItem([data["config name"]])
            self.tree.addTopLevelItem(tree_item)
        else:
            values.aircraft_configs[self.index] = data
            # TODO update config name if changed

    def load_data(self, data):
        self.name_line_edit.setText(data["config name"])
        
        assert self.cs_de_widget is not None and self.prop_de_widget is not None        
        self.cs_de_widget.load_data(data["cs deflections"])
        self.prop_de_widget.load_data(data["propulsors"])

    def on_tree_item_clicked(self, item : QTreeWidgetItem, _col):
        self.index = self.tree.indexOfTopLevelItem(item)
        self.load_data(values.aircraft_configs[self.index])


def get_widget() -> QWidget:
    return AircraftConfigsWidget()
