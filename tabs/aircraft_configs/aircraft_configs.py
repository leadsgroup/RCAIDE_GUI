# RCAIDE_GUI/tabs/aircraft_configs/aircraft_configs.py
#
# Created: Oct 2024, Laboratory for Electric Aircraft Design and Sustainability

import RCAIDE
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QLabel, QLineEdit, QCheckBox, QSpacerItem, QSizePolicy, QScrollArea, QGroupBox
)

from tabs import TabWidget
from utilities import Units
from widgets import DataEntryWidget
import values
from RCAIDE.Framework.Core import Data
import RCAIDE
import values

# Used if no configurations exist yet
_DEFAULT_CONFIG_NAMES = ["base", "cruise", "takeoff", "cutback", "landing", "reverse_thrust"]

class AircraftConfigsWidget(TabWidget):
    def __init__(self):
        super().__init__()

        # Index of the currently selected configuration
        self.index = -1

        # Stores widgets for each config so we can save later
        self._cfg_widgets = {}

        # --- Main layout ---
        base_layout = QHBoxLayout()

        # --- Configuration tree (left side) ---
        tree_layout = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Configuration Tree"])

        self.root_item = QTreeWidgetItem(["Aircraft Configurations"])
        self.tree.addTopLevelItem(self.root_item)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)

        tree_layout.addWidget(self.tree)

        # --- Configuration editor (right side) ---
        self.main_layout = QVBoxLayout()

        # Config name field (for selected config)
        name_layout = QHBoxLayout()
        self.name_line_edit = QLineEdit()
        name_layout.addWidget(QLabel("Config Name:"), 3)
        name_layout.addWidget(self.name_line_edit, 7)
        self.main_layout.addLayout(name_layout)

        self.main_layout.addWidget(QLabel("<b>All Configurations</b>"))

        # Scroll area that holds all config blocks
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll.setWidget(self.scroll_container)

        self.main_layout.addWidget(self.scroll)

        # Save / New buttons
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_data)
        self.main_layout.addWidget(save_btn)

        new_btn = QPushButton("New Configuration")
        new_btn.clicked.connect(self.new_configuration)
        self.main_layout.addWidget(new_btn)

        # Put everything together
        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(self.main_layout, 7)
        self.setLayout(base_layout)

        # Build UI after widget is fully created
        QTimer.singleShot(0, self.update_layout)

    def _ensure_config_data(self):
        # Make sure config_data exists
        if not isinstance(getattr(values, "config_data", None), list):
            values.config_data = []

        # If empty, create default configs
        if not values.config_data:
            values.config_data = [{
                "config name": n,
                "cs deflections": {},
                "propulsors": {},
                "gear down": False
            } for n in _DEFAULT_CONFIG_NAMES]

    def _ensure_geometry(self):
        if not isinstance(getattr(values, "geometry_data", None), list):
            values.geometry_data = [None] * 8

    def _discover_from_geometry(self):
        # Find all control surfaces and propulsors in geometry_data
        cs, props = set(), set()

        def walk(obj):
            # Walk through nested dicts/lists
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "control_surfaces" and isinstance(v, list):
                        for csd in v:
                            name = csd.get("CS name") or csd.get("name")
                            if name:
                                cs.add(name)

                    if k == "propulsor data" and isinstance(v, list):
                        for p in v:
                            tag = p.get("Propulsor Tag") or p.get("name")
                            if tag:
                                props.add(tag)

                    walk(v)

            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(values.geometry_data)
        return sorted(cs), sorted(props)

    def _build_labels(self):
        # Convert geometry names into DataEntryWidget labels
        cs_names, prop_names = self._discover_from_geometry()

        cs_labels = [(f"{n} Deflection", Units.Angle) for n in cs_names]
        prop_labels = [(f"{n} Enabled", Units.Boolean) for n in prop_names]

        return cs_labels, prop_labels

    def _normalize_cfg(self, cfg, cs_labels, prop_labels):
        # Ensure config has entries for all control surfaces
        cs_dict = cfg.setdefault("cs deflections", {})
        for label, _ in cs_labels:
            if label not in cs_dict:
                cs_dict[label] = (0.0, 0)

        # Ensure config has entries for all propulsors
        prop_dict = cfg.setdefault("propulsors", {})
        for label, _ in prop_labels:
            if label not in prop_dict:
                prop_dict[label] = (True, 0)

        # Ensure landing gear key exists
        cfg.setdefault("gear down", False)

    def update_layout(self):
        # Sync data and geometry
        self._ensure_geometry()
        self._ensure_config_data()

        cs_labels, prop_labels = self._build_labels()

        # Clear old widget references
        self._cfg_widgets.clear()

        # Clear scroll area
        while self.scroll_layout.count():
            w = self.scroll_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        # Clear tree
        self.root_item.takeChildren()

        # Build UI for each configuration
        for i, cfg in enumerate(values.config_data):
            self._normalize_cfg(cfg, cs_labels, prop_labels)

            name = cfg.get("config name", "Unnamed")
            group = QGroupBox(name)
            layout = QVBoxLayout(group)

            layout.addWidget(QLabel(f"Config Name: {name}"))

            # Control surfaces
            layout.addWidget(QLabel("<b>Control Surfaces</b>"))
            cs_block = None
            if cs_labels:
                cs_block = DataEntryWidget(cs_labels)
                cs_block.load_data(cfg["cs deflections"])
                layout.addWidget(cs_block)
            else:
                layout.addWidget(QLabel("<i>No control surfaces defined.</i>"))

            # Propulsors
            layout.addWidget(QLabel("<b>Propulsors</b>"))
            prop_block = None
            if prop_labels:
                prop_block = DataEntryWidget(prop_labels)
                prop_block.load_data(cfg["propulsors"])
                layout.addWidget(prop_block)
            else:
                layout.addWidget(QLabel("<i>No propulsors defined.</i>"))

            # Landing gear
            gear = QCheckBox("Landing Gear Deployed")
            gear.setChecked(cfg.get("gear down", False))
            layout.addWidget(gear)

            # Save widget references for this config
            self._cfg_widgets[i] = {
                "cs": cs_block,
                "prop": prop_block,
                "gear": gear
            }

            self.scroll_layout.addWidget(group)
            self.root_item.addChild(QTreeWidgetItem([name]))

        # Push content to the top
        self.scroll_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        self.tree.expandAll()

    def on_tree_item_clicked(self, item, _):
        # Update selected config when clicking the tree
        idx = self.root_item.indexOfChild(item)
        if idx >= 0:
            self.index = idx
            self.name_line_edit.setText(
                values.config_data[idx].get("config name", "")
            )

    def new_configuration(self):
        # Add a new empty config
        values.config_data.append({
            "config name": "new_config",
            "cs deflections": {},
            "propulsors": {},
            "gear down": False
        })
        self.index = len(values.config_data) - 1
        self.update_layout()

    def save_data(self):
        if self.index not in self._cfg_widgets:
            return
        w = self._cfg_widgets[self.index]
        cfg = values.config_data[self.index]

        # Update name
        cfg["config name"] = self.name_line_edit.text().strip() or cfg["config name"]

        # Control surfaces
        if w["cs"]:
            cfg["cs deflections"].update(w["cs"].get_values())

        # Propulsors
        if w["prop"]:
            cfg["propulsors"].update(w["prop"].get_values())

        # Landing gear
        cfg["gear down"] = w["gear"].isChecked()
        
        # --- Build RCAIDE solver configs ---
        try:
            # Import the config builder that converts geometry
            # into valid RCAIDE aircraft configuration objects
            from tabs.aircraft_configs.aircraft_configs import (
                build_rcaide_configs_from_geometry
            )

            # Build and store the aircraft configurations
            values.rcaide_configs = build_rcaide_configs_from_geometry()
            print("[OK] RCAIDE aircraft configs built")

        except Exception as e:
            # If config generation fails, continue execution
            # and report the failure without crashing the solver
            print("[WARN] Failed to build RCAIDE configs:", e)

def get_widget() -> QWidget:
    return AircraftConfigsWidget()
