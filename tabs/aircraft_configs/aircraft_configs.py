# RCAIDE_GUI/tabs/aircraft_configs/aircraft_configs.py

import RCAIDE
from RCAIDE.Library.Components.Configs.Config import Config

from tabs import TabWidget
from utilities import Units
from common_widgets import DataEntryWidget
import rcaide_io

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QLabel, QLineEdit, QCheckBox, QSpacerItem, QSizePolicy, QScrollArea, QGroupBox,
    QMessageBox, QInputDialog
)


class AircraftConfigsWidget(TabWidget):
    def __init__(self):
        super().__init__()
        self._cfg_widgets  = {}   # config tag → {name_edit, cs_block, prop_block, gear_check}
        self._selected_tag = None

        base_layout = QHBoxLayout()

        tree_layout = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Configuration Tree"])
        self.root_item = QTreeWidgetItem(["Aircraft Configurations"])
        self.tree.addTopLevelItem(self.root_item)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        tree_layout.addWidget(self.tree)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(QLabel("<b>All Configurations</b>"))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll.setWidget(self.scroll_container)
        self.main_layout.addWidget(self.scroll)

        button_layout = QHBoxLayout()
        new_btn = QPushButton("New Config")
        new_btn.clicked.connect(self.new_configuration)
        button_layout.addWidget(new_btn)
        save_btn = QPushButton("Save Config")
        save_btn.clicked.connect(self.save_data)
        button_layout.addWidget(save_btn)
        delete_btn = QPushButton("Delete Config")
        delete_btn.clicked.connect(self.delete_data)
        button_layout.addWidget(delete_btn)
        self.main_layout.addLayout(button_layout)

        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(self.main_layout, 7)
        self.setLayout(base_layout)

        QTimer.singleShot(0, self.update_layout)

    # ------------------------------------------------------------------
    #  Vehicle traversal helpers
    # ------------------------------------------------------------------

    def _cs_names(self):
        names = []
        for wing in getattr(rcaide_io.vehicle, 'wings', []):
            for cs in getattr(wing, 'control_surfaces', []):
                tag = getattr(cs, 'tag', None)
                if tag and tag not in names:
                    names.append(tag)
        return sorted(names)

    def _prop_names(self):
        names = []
        for network in getattr(rcaide_io.vehicle, 'networks', []):
            for prop in getattr(network, 'propulsors', []):
                tag = getattr(prop, 'tag', None)
                if tag and tag not in names:
                    names.append(tag)
        return sorted(names)

    def _get_cs_deflection(self, config, cs_name):
        for wing in getattr(config, 'wings', []):
            for cs in getattr(wing, 'control_surfaces', []):
                if getattr(cs, 'tag', None) == cs_name:
                    return getattr(cs, 'deflection', 0.0)
        return 0.0

    def _set_cs_deflection(self, config, cs_name, angle):
        for wing in getattr(config, 'wings', []):
            for cs in getattr(wing, 'control_surfaces', []):
                if getattr(cs, 'tag', None) == cs_name:
                    cs.deflection = angle
                    return

    def _get_gear_extended(self, config):
        for gear in getattr(config, 'landing_gears', []):
            if getattr(gear, 'gear_extended', False):
                return True
        return False

    def _set_gear_extended(self, config, value):
        for gear in getattr(config, 'landing_gears', []):
            gear.gear_extended = value

    def _get_prop_active(self, config, prop_name):
        for network in getattr(config, 'networks', []):
            for prop in getattr(network, 'propulsors', []):
                if getattr(prop, 'tag', None) == prop_name:
                    return getattr(prop, 'active', True)
        return True

    def _set_prop_active(self, config, prop_name, value):
        for network in getattr(config, 'networks', []):
            for prop in getattr(network, 'propulsors', []):
                if getattr(prop, 'tag', None) == prop_name:
                    if hasattr(prop, 'active'):
                        prop.active = bool(value)
                    return

    # ------------------------------------------------------------------
    #  Layout
    # ------------------------------------------------------------------

    def update_layout(self):
        cs_names   = self._cs_names()
        prop_names = self._prop_names()
        cs_labels   = [(f"{n} Deflection", Units.Angle)   for n in cs_names]
        prop_labels = [(f"{n} Enabled",    Units.Boolean) for n in prop_names]

        self._cfg_widgets.clear()
        while self.scroll_layout.count():
            w = self.scroll_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.root_item.takeChildren()

        configs = rcaide_io.rcaide_configs
        for cfg_tag, config in configs.items():
            if not hasattr(config, 'tag'):
                continue
            name = config.tag

            group  = QGroupBox(name)
            layout = QVBoxLayout(group)

            name_row = QHBoxLayout()
            name_row.addWidget(QLabel("Config Name:"))
            name_edit = QLineEdit(name)
            name_row.addWidget(name_edit)
            layout.addLayout(name_row)

            layout.addWidget(QLabel("<b>Control Surfaces</b>"))
            cs_block = None
            if cs_labels:
                cs_block = DataEntryWidget(cs_labels)
                cs_block.load_data({
                    f"{n} Deflection": [self._get_cs_deflection(config, n), 0]
                    for n in cs_names
                })
                layout.addWidget(cs_block)
            else:
                layout.addWidget(QLabel("<i>No control surfaces defined.</i>"))

            layout.addWidget(QLabel("<b>Propulsors</b>"))
            prop_block = None
            if prop_labels:
                prop_block = DataEntryWidget(prop_labels)
                prop_block.load_data({
                    f"{n} Enabled": [self._get_prop_active(config, n), 0]
                    for n in prop_names
                })
                layout.addWidget(prop_block)
            else:
                layout.addWidget(QLabel("<i>No propulsors defined.</i>"))

            gear_check = QCheckBox("Landing Gear Deployed")
            gear_check.setChecked(self._get_gear_extended(config))
            layout.addWidget(gear_check)

            self._cfg_widgets[name] = {
                "name":      name_edit,
                "cs":        cs_block,
                "prop":      prop_block,
                "gear":      gear_check,
                "orig_tag":  cfg_tag,
            }

            self.scroll_layout.addWidget(group)
            self.root_item.addChild(QTreeWidgetItem([name]))

        self.scroll_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        self.tree.expandAll()

    def on_tree_item_clicked(self, item, _):
        idx  = self.root_item.indexOfChild(item)
        tags = list(self._cfg_widgets.keys())
        self._selected_tag = tags[idx] if 0 <= idx < len(tags) else None

    # ------------------------------------------------------------------
    #  CRUD
    # ------------------------------------------------------------------

    def new_configuration(self):
        name, ok = QInputDialog.getText(self, "New Configuration", "Configuration name:")
        if not ok:
            return
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Configuration name cannot be empty.")
            return
        if any(getattr(c, 'tag', '') == name for _, c in rcaide_io.rcaide_configs.items()):
            QMessageBox.warning(self, "Duplicate Name", "Configuration name already exists.")
            return

        config     = Config(rcaide_io.vehicle)
        config.tag = name
        rcaide_io.rcaide_configs.append(config)
        self._selected_tag = name
        self.update_layout()

    def save_data(self):
        new_configs = Config.Container()
        for name, w in self._cfg_widgets.items():
            orig_tag = w["orig_tag"]
            try:
                config = rcaide_io.rcaide_configs[orig_tag]
            except (KeyError, TypeError):
                continue

            new_name   = w["name"].text().strip() or name
            config.tag = new_name

            if w["cs"]:
                for label, val in w["cs"].get_values().items():
                    if label.endswith(" Deflection"):
                        cs_name = label[: -len(" Deflection")]
                        angle   = val[0] if isinstance(val, (list, tuple)) else val
                        self._set_cs_deflection(config, cs_name, angle)

            if w["prop"]:
                for label, val in w["prop"].get_values().items():
                    if label.endswith(" Enabled"):
                        prop_name = label[: -len(" Enabled")]
                        active    = val[0] if isinstance(val, (list, tuple)) else val
                        self._set_prop_active(config, prop_name, active)

            self._set_gear_extended(config, w["gear"].isChecked())
            new_configs.append(config)

        rcaide_io.rcaide_configs   = new_configs
        rcaide_io.propulsor_names  = _collect_propulsor_names(rcaide_io.vehicle)
        self.update_layout()
        QMessageBox.information(self, "Saved", "Aircraft configurations saved.")

    def delete_data(self):
        if self._selected_tag is None:
            return
        orig_tag = (self._cfg_widgets.get(self._selected_tag) or {}).get("orig_tag")
        key = orig_tag or self._selected_tag
        try:
            del rcaide_io.rcaide_configs[key]
        except (KeyError, TypeError, AttributeError):
            pass
        self._selected_tag = None
        self.update_layout()


# ------------------------------------------------------------------------------
#  Module-level helpers
# ------------------------------------------------------------------------------

def _collect_propulsor_names(vehicle):
    names = [[]]
    for network in getattr(vehicle, 'networks', []):
        for prop in getattr(network, 'propulsors', []):
            names[0].append(prop.tag)
    return names


def build_rcaide_configs_from_geometry():
    """
    Return the current RCAIDE Config.Container, collecting propulsor names as a
    side effect.  Raises RuntimeError if no vehicle or configs are available.
    """
    if rcaide_io.vehicle is None:
        raise RuntimeError("No geometry data available")
    if not rcaide_io.rcaide_configs:
        raise RuntimeError("No aircraft configurations available")

    rcaide_io.propulsor_names = _collect_propulsor_names(rcaide_io.vehicle)
    return rcaide_io.rcaide_configs


def get_widget() -> QWidget:
    return AircraftConfigsWidget()
