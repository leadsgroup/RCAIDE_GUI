from PyQt6.QtWidgets import QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, \
                                QLabel, QLineEdit, QCheckBox, QSpacerItem, QSizePolicy

from tabs import TabWidget
from utilities import Units, create_line_bar, convert_name
from widgets import DataEntryWidget
import values

import RCAIDE
from RCAIDE.Library.Methods.Stability.Center_of_Gravity import compute_component_centers_of_gravity


class AircraftConfigsWidget(TabWidget):
    def __init__(self):
        super().__init__()
        self.vehicle = None
        self.data = None

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

        self.main_layout.addWidget(QLabel("<b>Landing Gear</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.landing_gear_down = QCheckBox("Landing Gear Down")
        self.main_layout.addWidget(self.landing_gear_down)
        self.main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))

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

        self.control_surface_data = []
        self.propulsor_data = []

        for wing in self.data[2]:
            for control_surface in wing["control_surfaces"]:
                control_surface["wing name"] = wing["name"]
                self.control_surface_data.append(control_surface)

        for energy_network in self.data[5]:
            for fuel_line in energy_network["energy_network"]:
                for propulsor in fuel_line["propulsor data"]:
                    propulsor["fuel line name"] = fuel_line["name"]
                    self.propulsor_data.append(propulsor)

        cs_deflections_labels = []
        propulsor_labels = []
        propulsor_data = {}
        for control_surface in self.control_surface_data:
            cs_deflections_labels.append(
                (control_surface["CS name"] + " Deflection", Units.Angle)
            )

        for propulsor in self.propulsor_data:
            field_name = propulsor["propulsor name"] + " Enabled"
            propulsor_labels.append(
                (field_name, Units.Boolean)
            )
            propulsor_data[field_name] = True, 0

        if self.cs_de_widget is not None:
            self.main_layout.removeWidget(self.cs_de_widget)
            self.main_layout.removeWidget(self.prop_de_widget)

        self.cs_de_widget = DataEntryWidget(cs_deflections_labels)
        self.main_layout.insertWidget(3, self.cs_de_widget)

        self.prop_de_widget = DataEntryWidget(propulsor_labels)
        self.prop_de_widget.load_data(propulsor_data)
        self.main_layout.insertWidget(6, self.prop_de_widget)

    def new_configuration(self):
        assert self.cs_de_widget is not None and self.prop_de_widget is not None
        self.cs_de_widget.clear_values()
        self.cs_de_widget.clear_values()
        self.name_line_edit.clear()

        self.index = -1

    def get_data(self):
        data = {}
        data["config name"] = self.name_line_edit.text()

        assert self.cs_de_widget is not None and self.prop_de_widget is not None
        data["cs deflections"] = self.cs_de_widget.get_values()
        data["propulsors"] = self.prop_de_widget.get_values()
        data["gear down"] = self.landing_gear_down.isChecked()

        return data

    def create_rcaide_structure(self):
        values.vehicle.center_of_gravity()
        compute_component_centers_of_gravity(values.vehicle)

        assert self.cs_de_widget is not None and self.prop_de_widget is not None

        config = RCAIDE.Library.Components.Configs.Config(values.vehicle)
        config.tag = self.name_line_edit.text()
        cs_values = self.cs_de_widget.get_values_si()
        for index, cs in enumerate(cs_values.items()):
            cs_data = self.control_surface_data[index]
            wing_name = convert_name(cs_data["wing name"])
            cs_name = convert_name(cs_data["CS name"])
            config.wings[wing_name].control_surfaces[cs_name].deflection = cs[1][0]

        prop_values = self.prop_de_widget.get_values_si()
        for index, prop in enumerate(prop_values.items()):
            prop_data = self.propulsor_data[index]
            fuel_line_name = convert_name(prop_data["fuel line name"])
            prop_name = convert_name(prop_data["propulsor name"])
            config.networks.fuel.fuel_lines[fuel_line_name].propulsors[prop_name].enabled = prop[1][0]
        
        config.landing_gear.gear_condition = 'down' if self.landing_gear_down.isChecked() else 'up'
        return config

    def save_data(self):
        data = self.get_data()
        config = self.create_rcaide_structure()
        if self.index == -1:
            self.index = len(values.config_data)
            values.config_data.append(data)
            values.rcaide_configs.append(config)
            tree_item = QTreeWidgetItem([data["config name"]])
            self.tree.addTopLevelItem(tree_item)
        else:
            values.config_data[self.index] = data
            # TODO update config if changed

    def load_data(self, data):
        self.name_line_edit.setText(data["config name"])
        assert self.cs_de_widget is not None and self.prop_de_widget is not None
        self.cs_de_widget.load_data(data["cs deflections"])
        self.prop_de_widget.load_data(data["propulsors"])
        self.landing_gear_down.setChecked(data["gear down"])

    def on_tree_item_clicked(self, item: QTreeWidgetItem, _col):
        self.index = self.tree.indexOfTopLevelItem(item)
        self.load_data(values.config_data[self.index])

    def load_from_values(self):
        self.tree.clear()
        self.index = -1
        for config in values.config_data:
            tree_item = QTreeWidgetItem([config["config name"]])
            self.tree.addTopLevelItem(tree_item)


def get_widget() -> QWidget:
    return AircraftConfigsWidget()
