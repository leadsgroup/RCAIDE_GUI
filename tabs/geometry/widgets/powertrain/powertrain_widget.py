# RCAIDE_GUI/tabs/geometry/widgets/powertrain/powertrain_widget.py

# Created: Dec 2025, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
# RCAIDE imports
import RCAIDE

_Battery = RCAIDE.Library.Components.Powertrain.Sources.Battery_Modules.Generic_Battery_Module

# Maps UI network type name → RCAIDE network class.
_NETWORK_CLASS_MAP = {
    "Fuel":      RCAIDE.Framework.Networks.Fuel,
    "Electric":  RCAIDE.Framework.Networks.Electric,
    "Hybrid":    RCAIDE.Framework.Networks.Hybrid,
    "Hydrogen":  RCAIDE.Framework.Networks.Hydrogen,
    "Fuel Cell": RCAIDE.Framework.Networks.Fuel_Cell,
}

from utilities import BTN_STYLE

def _distributor_container(distributor):
    """Return the Network attribute name that holds this distributor type."""
    if isinstance(distributor, RCAIDE.Library.Components.Powertrain.Distributors.Electrical_Bus):
        return "busses"
    if isinstance(distributor, RCAIDE.Library.Components.Powertrain.Distributors.Coolant_Line):
        return "coolant_lines"
    return "fuel_lines"

# PyQT imports
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QTabWidget

# RCAIDE GUI Imports
from tabs.geometry.frames.powertrain.sources import EnergySourceFrame
from tabs.geometry.frames.powertrain.distributors import DistributorFrame
from tabs.geometry.frames.powertrain.converters import ConverterFrame
from tabs.geometry.frames.powertrain.propulsors import PropulsorFrame
from tabs.geometry.frames.powertrain.systems import SystemFrame
from common_widgets import DataEntryWidget


# ----------------------------------------------------------------------------------------------------------------------
#  Powertrain Widget
# ---------------------------------------------------------------------------------------------------------------------
class PowertrainWidget(QWidget):
    """Tab-based editor for a single RCAIDE energy network.

    Contains five sub-tabs: Distributors, Energy Sources, Propulsors, Systems,
    and Converters — each backed by its own frame class.  A "Refresh
    Connections" button propagates current propulsor and source names into
    every distributor's inline checkbox rows.

    ``network_type`` must be set by the parent (``PowertrainFrame``) before
    ``get_data_values()`` is called so the correct RCAIDE network class is
    instantiated (``_NETWORK_CLASS_MAP``).

    Backwards-compatible with old GUI saves that stored connectivity as a
    matrix under ``"connections"``; ``_migrate_connections()`` converts these
    on load.
    """

    def __init__(self):
        super(PowertrainWidget, self).__init__()

        self.network_type = "Fuel"
        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        layout = self.create_scroll_layout()

        name_layout = QHBoxLayout()
        layout.addLayout(name_layout)

        # ── Tabs ───────────────────────────────────────────────────────────
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.distributor_frame = DistributorFrame()
        self.tab_widget.addTab(self.distributor_frame, "Distributors")

        self.energy_source_frame = EnergySourceFrame()
        self.tab_widget.addTab(self.energy_source_frame, "Energy Sources")

        self.propulsor_frame = PropulsorFrame()
        self.tab_widget.addTab(self.propulsor_frame, "Propulsors")

        self.system_frame = SystemFrame()
        self.tab_widget.addTab(self.system_frame, "Systems")

        self.converter_frame = ConverterFrame()
        self.tab_widget.addTab(self.converter_frame, "Converters")

        # ── Refresh Connections button ─────────────────────────────────────
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line_bar)

        refresh_btn = QPushButton("Refresh Connections")
        refresh_btn.setStyleSheet(BTN_STYLE)
        refresh_btn.setToolTip(
            "Sync propulsor and source names into each distributor's inline checkboxes."
        )
        refresh_btn.clicked.connect(self._refresh_connections)
        layout.addWidget(refresh_btn)

    # ── Connection refresh ─────────────────────────────────────────────────

    def _refresh_connections(self):
        """Push current propulsor & source names into each distributor's inline checkboxes.

        Reads names directly from each widget's name field to avoid triggering
        expensive RCAIDE design calls (e.g. design_turbofan) just to get a tag.
        """
        propulsor_names = self._collect_names(self.propulsor_frame.propulsor_sections_layout)
        source_names    = self._collect_names(self.energy_source_frame.source_sections_layout)
        self.distributor_frame.refresh_connections(propulsor_names, source_names)

    @staticmethod
    def _collect_names(layout):
        """Return the section_name_edit text for every widget in *layout*."""
        names = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None and hasattr(widget, "section_name_edit"):
                names.append(widget.section_name_edit.text())
        return names

    # ── Data API ───────────────────────────────────────────────────────────

    def get_data_values(self, just_data=False):
        """Retrieve data from all tabs and build the RCAIDE network."""
        data = {}

        data["distributor data"], distributors = self.distributor_frame.get_data_values()
        data["source data"],      sources      = self.energy_source_frame.get_data_values()
        data["propulsor data"],   propulsors   = self.propulsor_frame.get_data_values()
        data["system data"],      systems      = self.system_frame.get_data_values()
        data["converter data"],   converters   = self.converter_frame.get_data_values()

        if just_data:
            return data

        net = self.create_rcaide_structure(data, distributors, sources, propulsors, converters, systems)
        return data, net

    def create_rcaide_structure(self, data, distributors, sources, propulsors, converters, systems):
        net_class = _NETWORK_CLASS_MAP.get(self.network_type, RCAIDE.Framework.Networks.Fuel)
        net = net_class()

        for propulsor in propulsors:
            net.propulsors.append(propulsor)

        source_by_tag = {s.tag: s for s in sources}
        distributor_data_list = data.get("distributor data", [])

        for d_data, distributor in zip(distributor_data_list, distributors):
            assigned = d_data.get("assigned_propulsors", [])
            distributor.assigned_propulsors = [assigned]  # RCAIDE expects [[tag, ...]]

            for src_name in d_data.get("assigned_sources", []):
                src = source_by_tag.get(src_name)
                if src is None:
                    continue
                if isinstance(src, _Battery):
                    distributor.battery_modules.append(src)
                else:
                    distributor.fuel_tanks.append(src)

            getattr(net, _distributor_container(distributor)).append(distributor)

        for converter in converters:
            converter.assigned_propulsors = [[]]
            net.converters.append(converter)

        for system in systems:
            net.systems.append(system)

        return net

    def load_data_values(self, data, index=0):
        # Migrate old-style connections matrix to inline format so saved files load cleanly.
        self._migrate_connections(data)

        self.distributor_frame.load_data(data.get("distributor data", []))
        self.energy_source_frame.load_data(data.get("source data", []))
        self.propulsor_frame.load_data(data.get("propulsor data", []))
        self.system_frame.load_data(data.get("system data", []))
        converter_data = data.get("converter data", data.get("converter  data", []))
        self.converter_frame.load_data(converter_data)

        # Auto-refresh so distributor checkboxes are populated immediately.
        self._refresh_connections()

    @staticmethod
    def _migrate_connections(data):
        """Convert old connections-matrix format into inline assigned_propulsors/assigned_sources."""
        connections = data.get("connections")
        if not connections:
            return
        propulsor_names = [d.get("Propulsor Tag", "") for d in data.get("propulsor data", [])]
        source_names    = [d.get("Source Name",   "") for d in data.get("source data",    [])]
        prop_conn = connections[0] if len(connections) > 0 else []
        src_conn  = connections[2] if len(connections) > 2 else []
        for i, d_item in enumerate(data.get("distributor data", [])):
            if "assigned_propulsors" not in d_item:
                row = prop_conn[i] if i < len(prop_conn) else []
                d_item["assigned_propulsors"] = [
                    propulsor_names[j] for j, checked in enumerate(row) if checked
                ]
            if "assigned_sources" not in d_item:
                row = src_conn[i] if i < len(src_conn) else []
                d_item["assigned_sources"] = [
                    source_names[j] for j, checked in enumerate(row) if checked
                ]

    def create_scroll_layout(self):
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        self.setLayout(layout)
        return layout
