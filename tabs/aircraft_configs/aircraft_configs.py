from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QLabel, QLineEdit, QCheckBox, QSpacerItem, QSizePolicy, QDockWidget, QTreeWidgetItem, QMenuBar, QGroupBox,
    QFormLayout
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from tabs import TabWidget
from utilities import Units, create_line_bar, convert_name
from widgets import DataEntryWidget
import values

from RCAIDE.Library.Methods.Stability.Center_of_Gravity import compute_component_centers_of_gravity
from widgets.collapsible_section import CollapsibleSection


class AircraftConfigsWidget(TabWidget):
    def __init__(self):
        super().__init__()
        self.main_window = AircraftConfigsMainWindow()
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.main_window)
        self.setLayout(layout)

class AircraftConfigsMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.vehicle = None
        self.data = None
        self.cs_de_widget = None
        self.prop_de_widget = None

        self.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks 
            | QMainWindow.DockOption.AllowTabbedDocks 
            | QMainWindow.DockOption.AnimatedDocks
        )

        self.create_tree_dock()
        self.create_config_dock()

    def create_tree_dock(self):
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Vehicle Configurations"])
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        tree_layout.addWidget(self.tree)

        self.tree_dock = QDockWidget("Vehicle Configurations", self)
        self.tree_dock.setObjectName("vehicle_configs_dock")

        self.tree_dock.setWidget(tree_container)
        self.tree_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable  
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tree_dock)

    def create_config_dock(self):
        # Configurations container
        configs_widget = QWidget()
        self.content_layout = QVBoxLayout(configs_widget)

        self.name_line_edit = QLineEdit()
        name_layout = QHBoxLayout()

        name_layout.addWidget(QLabel("Config Name:"), 3)
        name_layout.addWidget(self.name_line_edit, 7)
        self.content_layout.addLayout(name_layout)

        self.content_layout.addWidget(QLabel("<b>Control Surfaces</b>"))
        self.content_layout.addWidget(create_line_bar())

        self.content_layout.addWidget(QLabel("<b>Propulsors</b>"))
        self.content_layout.addWidget(create_line_bar())

        self.content_layout.addWidget(QLabel("<b>Landing Gear</b>"))
        self.content_layout.addWidget(create_line_bar())
        self.landing_gear_down = QCheckBox("Landing Gear Down")
        self.content_layout.addWidget(self.landing_gear_down)
        self.content_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))

        self.update_layout()

        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_data)
        self.content_layout.addWidget(save_button)

        new_config_button = QPushButton("New Configuration")
        new_config_button.clicked.connect(self.new_configuration)
        self.content_layout.addWidget(new_config_button)

        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        collapsible = CollapsibleSection("Configuration", configs_widget)

        container_widget = QWidget() 
        container_layout = QVBoxLayout(container_widget)

        container_layout.addWidget(collapsible)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create the dockable configurations view
        self.config_dock = QDockWidget("Configuration Details", self)
        self.config_dock.setObjectName("config_details_dock")

        self.config_dock.setWidget(container_widget)
        self.config_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable 
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.config_dock)


    def reset_layout(self):
        # Restore the saved default layout
        self.restoreState(self.default_layout)

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
            self.content_layout.removeWidget(self.cs_de_widget)
            self.content_layout.removeWidget(self.prop_de_widget)

        self.cs_de_widget = DataEntryWidget(cs_deflections_labels)
        self.content_layout.insertWidget(3, self.cs_de_widget)

        self.prop_de_widget = DataEntryWidget(propulsor_labels)
        self.prop_de_widget.load_data(propulsor_data)
        self.content_layout.insertWidget(3, self.cs_de_widget)

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

    def load_data(self, data):
        self.name_line_edit.setText(data["config name"])
        assert self.cs_de_widget is not None and self.prop_de_widget is not None
        self.cs_de_widget.load_data(data["cs deflections"])
        self.prop_de_widget.load_data(data["propulsors"])
        self.landing_gear_down.setChecked(data["gear down"])

    def on_tree_item_clicked(self, item: QTreeWidgetItem, _col):
        self.index = self.tree.indexOfTopLevelItem(item)
        self.load_data(values.config_data[self.index])


def get_widget() -> QWidget:
    return AircraftConfigsWidget()