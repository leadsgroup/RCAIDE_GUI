# RCAIDE_GUI/tabs/aircraft_configs/aircraft_configs.py
#
# Created: Oct 2024, Laboratry for Electric Aircraft Design and Sustainabiltiy

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------
# RCAIDE imports  
import RCAIDE

# PtQt imports  
from PyQt6.QtWidgets import QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, \
                                QLabel, QLineEdit, QCheckBox, QSpacerItem, QSizePolicy, QScrollArea, QGroupBox
#                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                                   added QScrollArea, QGroupBox for (12)

# gui imports
from tabs import TabWidget
from utilities import Units, create_line_bar, convert_name
from widgets import DataEntryWidget
import values


# ----------------------------------------------------------------------------------------------------------------------
#  AircraftConfigsWidget
# ----------------------------------------------------------------------------------------------------------------------
class AircraftConfigsWidget(TabWidget):
    def __init__(self):
        super().__init__()
        self.vehicle = None
        self.data = None

        self.cs_de_widget = None
        self.prop_de_widget = None

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()

        # Left-side configuration tree
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Configuration Tree"])
        self.root_item = QTreeWidgetItem(["Aircraft Configurations"])
        self.tree.addTopLevelItem(self.root_item)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        tree_layout.addWidget(self.tree)

        # Right-side main layout
        self.main_layout = QVBoxLayout()
        self.name_line_edit = QLineEdit()
        name_layout = QHBoxLayout()

        name_layout.addWidget(QLabel("Config Name:"), 3)
        name_layout.addWidget(self.name_line_edit, 7)
        self.main_layout.addLayout(name_layout)

        # --- Removed top duplicated control surfaces and propulsors sections ---
        # (previously above the scroll area)

        # Scrollable section to display all configs
        self.main_layout.addWidget(QLabel("<b>All Configurations</b>"))
        self.all_configs_scroll = QScrollArea()
        self.all_configs_scroll.setWidgetResizable(True)
        self.all_configs_container = QWidget()
        self.all_configs_layout = QVBoxLayout(self.all_configs_container)
        self.all_configs_layout.setSpacing(8)
        self.all_configs_scroll.setWidget(self.all_configs_container)
        self.main_layout.addWidget(self.all_configs_scroll)

        self.update_layout()

        # Save / New buttons
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
            propulsor_labels.append((field_name, Units.Boolean))
            propulsor_data[field_name] = True, 0

        # Remove duplicated widgets (if any were present)
        if self.cs_de_widget is not None:
            self.main_layout.removeWidget(self.cs_de_widget)
            self.main_layout.removeWidget(self.prop_de_widget)

        # Clean and rebuild scroll area
        while self.all_configs_layout.count():
            item = self.all_configs_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for cfg in values.config_data:
            group = QGroupBox(cfg["config name"])
            g_layout = QVBoxLayout(group)

            # Config name
            g_layout.addWidget(QLabel(f"Config Name: {cfg['config name']}"))

            # Control Surfaces
            cs_block = DataEntryWidget(cs_deflections_labels)
            cs_block.load_data(cfg.get("cs deflections", {}))
            g_layout.addWidget(QLabel("<b>Control Surfaces</b>"))
            g_layout.addWidget(cs_block)

            # Propulsors
            prop_block = DataEntryWidget(propulsor_labels)
            prop_block.load_data(cfg.get("propulsors", {}))
            g_layout.addWidget(QLabel("<b>Propulsors</b>"))
            g_layout.addWidget(prop_block)

            # Landing Gear (inside scroll)
            g_layout.addWidget(QLabel("<b>Landing Gear</b>"))
            landing_checkbox = QCheckBox("Landing Gear Deployed")
            landing_checkbox.setChecked(cfg.get("gear down", False))
            g_layout.addWidget(landing_checkbox)

            self.all_configs_layout.addWidget(group)

        self.all_configs_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Rebuild the tree
        self.root_item.takeChildren()
        for cfg in values.config_data:
            self.root_item.addChild(QTreeWidgetItem([cfg["config name"]]))
        self.tree.expandAll()

    def new_configuration(self):
        assert self.cs_de_widget is not None and self.prop_de_widget is not None
        self.cs_de_widget.clear_values()
        self.cs_de_widget.clear_values()
        self.name_line_edit.clear()
        self.index = -1

    def get_data(self):
        data = {}
        data["config name"] = self.name_line_edit.text()
        data["cs deflections"] = self.cs_de_widget.get_values() if self.cs_de_widget else {}
        data["propulsors"] = self.prop_de_widget.get_values() if self.prop_de_widget else {}
        data["gear down"] = False
        return data

    def create_rcaide_structure(self):
        config = RCAIDE.Library.Components.Configs.Config(values.vehicle)
        config.tag = self.name_line_edit.text()
        config.landing_gear.gear_condition = 'deployed'
        return config

    def save_data(self):
        data = self.get_data()
        config = self.create_rcaide_structure()
        if self.index == -1:
            self.index = len(values.config_data)
            values.config_data.append(data)
            values.rcaide_configs.append(config)
            tree_item = QTreeWidgetItem([data["config name"]])
            self.root_item.addChild(tree_item)
        else:
            values.config_data[self.index] = data
        self.update_layout()

    def load_data(self, data):
        self.name_line_edit.setText(data["config name"])

    def on_tree_item_clicked(self, item: QTreeWidgetItem, _col):
        self.index = self.tree.indexOfTopLevelItem(item)
        self.load_data(values.config_data[self.index])

    def load_from_values(self):
        self.tree.clear()
        self.index = -1
        self.root_item = QTreeWidgetItem(["Aircraft Configurations"])
        self.tree.addTopLevelItem(self.root_item)

        for config in values.config_data:
            tree_item = QTreeWidgetItem([config["config name"]])
            self.root_item.addChild(tree_item)

            widget = AircraftConfigsWidget()
            widget.load_data(config)
            values.rcaide_configs.append(widget.create_rcaide_structure())
            widget.deleteLater()

        self.tree.expandAll()
        self.update_layout()


def get_widget() -> QWidget:
    return AircraftConfigsWidget()
