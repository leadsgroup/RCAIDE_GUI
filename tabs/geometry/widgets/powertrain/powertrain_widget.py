# RCAIDE_GUI/tabs/geometry/widgets/powertrain/powertrain_widget.py

# Created: Dec 2025, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE

_Battery = RCAIDE.Library.Components.Powertrain.Sources.Battery_Modules.Generic_Battery_Module

_NETWORK_CLASS_MAP = {
    "Fuel":      RCAIDE.Framework.Networks.Fuel,
    "Electric":  RCAIDE.Framework.Networks.Electric,
    "Hybrid":    RCAIDE.Framework.Networks.Hybrid,
    "Hydrogen":  RCAIDE.Framework.Networks.Hydrogen,
    "Fuel Cell": RCAIDE.Framework.Networks.Fuel_Cell,
}

from utilities import BTN_STYLE

def _distributor_container(distributor):
    if isinstance(distributor, RCAIDE.Library.Components.Powertrain.Distributors.Electrical_Bus):
        return "busses"
    if isinstance(distributor, RCAIDE.Library.Components.Powertrain.Distributors.Coolant_Line):
        return "coolant_lines"
    return "fuel_lines"

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QTabWidget

from tabs.geometry.frames.powertrain.sources      import EnergySourceFrame
from tabs.geometry.frames.powertrain.distributors import DistributorFrame
from tabs.geometry.frames.powertrain.converters   import ConverterFrame
from tabs.geometry.frames.powertrain.propulsors   import PropulsorFrame
from tabs.geometry.frames.powertrain.systems      import SystemFrame
from tabs.geometry.frames.powertrain.connections  import ConnectionMatrixFrame
from tabs.geometry.frames.powertrain.connections.powertrain_diagram import PowertrainDiagramWidget
from tabs.geometry.widgets.powertrain.distributors.base_distributor_widget import BaseDistributorWidget
from common_widgets import DataEntryWidget


class PowertrainWidget(QWidget):
    """Tab-based editor for a single RCAIDE energy network.

    Contains six sub-tabs: Distributors, Energy Sources, Propulsors, Systems,
    Converters, and Connections.  The Connections tab shows a matrix of
    Propulsors × Distributors and Sources × Distributors so that many-to-many
    connectivity can be visualised and edited in one place.

    ``network_type`` must be set by the parent (``PowertrainFrame``) before
    ``get_data_values()`` is called so the correct RCAIDE network class is
    instantiated (``_NETWORK_CLASS_MAP``).
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

        self.propulsor_frame = PropulsorFrame()
        self.tab_widget.addTab(self.propulsor_frame, "Propulsors")

        self.energy_source_frame = EnergySourceFrame()
        self.tab_widget.addTab(self.energy_source_frame, "Energy Sources")

        self.system_frame = SystemFrame()
        self.tab_widget.addTab(self.system_frame, "Flight Systems")

        self.converter_frame = ConverterFrame()
        self.tab_widget.addTab(self.converter_frame, "Converters")

        self.connection_matrix_frame = ConnectionMatrixFrame()
        self.tab_widget.addTab(self.connection_matrix_frame, "Connections")

        # Show the same network data as a node-and-edge diagram.  The diagram
        # is refreshed alongside the connection matrix in _refresh_matrix().
        self.powertrain_diagram = PowertrainDiagramWidget()
        self.tab_widget.addTab(self.powertrain_diagram, "Network Diagram")

        # Auto-refresh matrix when the user switches to the Connections tab
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # ── Refresh Connections button ─────────────────────────────────────
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line_bar)

        refresh_btn = QPushButton("Refresh Connections")
        refresh_btn.setStyleSheet(BTN_STYLE)
        refresh_btn.setToolTip(
            "Sync component names into the Connections matrix."
        )
        refresh_btn.clicked.connect(self._refresh_matrix)
        layout.addWidget(refresh_btn)

    # ── Tab change ─────────────────────────────────────────────────────────

    def _on_tab_changed(self, index):
        if self.tab_widget.widget(index) is self.connection_matrix_frame:
            self._refresh_matrix()

    # ── Matrix refresh ─────────────────────────────────────────────────────

    def _refresh_matrix(self):
        """Rebuild the connection matrix from current component names and
        any previously saved connectivity data."""
        propulsor_names  = self._collect_names(self.propulsor_frame.propulsor_sections_layout)
        source_names     = self._collect_names(self.energy_source_frame.source_sections_layout)
        distributor_names, connectivity = self._collect_distributor_info()
        converter_names = self._collect_names(self.converter_frame.converter_sections_layout)
        system_names = self._collect_names(self.system_frame.systems_layout)

        # Preserve each component's concrete editor type so the diagram can
        # distinguish components that share the same broad powertrain group.
        component_types = {}
        component_types.update(self._collect_types(self.energy_source_frame.source_sections_layout))
        component_types.update(self._collect_types(self.distributor_frame.distributor_sections_layout))
        component_types.update(self._collect_types(self.propulsor_frame.propulsor_sections_layout))

        # Keep the editable matrix and its visual representation synchronized
        # from one snapshot of the current component names and connections.
        self.connection_matrix_frame.refresh(
            propulsor_names, source_names, distributor_names, connectivity
        )
        self.powertrain_diagram.refresh(
            propulsor_names, source_names, distributor_names, connectivity,
            converter_names, system_names, component_types,
        )

    def _collect_distributor_info(self) -> tuple[list[str], dict]:
        """Return (ordered list of distributor names, connectivity dict).

        connectivity[dist_name] = {
            'assigned_propulsors': [...],
            'assigned_sources':    [...],
        }
        """
        names = []
        connectivity: dict[str, dict] = {}
        layout = self.distributor_frame.distributor_sections_layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if not isinstance(widget, BaseDistributorWidget):
                continue
            if not hasattr(widget, "section_name_edit"):
                continue
            name = widget.section_name_edit.text()
            names.append(name)
            # Read connectivity stored during load_data_values (or empty for new widgets)
            connectivity[name] = {
                "assigned_propulsors": list(getattr(widget, "_loaded_propulsors", [])),
                "assigned_sources":    list(getattr(widget, "_loaded_sources",    [])),
            }
        return names, connectivity

    @staticmethod
    def _collect_names(layout) -> list[str]:
        """Return displayed names for all component editors in a layout.

        Component widgets are not fully uniform: most expose
        ``section_name_edit``, while some use ``name_edit`` instead.
        """
        names = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is None:
                continue
            name_field = getattr(widget, "section_name_edit", None)
            if name_field is None:
                name_field = getattr(widget, "name_edit", None)
            if name_field is not None:
                names.append(name_field.text())
        return names

    @staticmethod
    def _collect_types(layout) -> dict[str, str]:
        """Map displayed component names to their concrete editor widget type.

        The widget class name is used as lightweight type metadata by the
        network diagram; the underlying component objects are not needed.
        """
        result = {}
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is None:
                continue
            name_field = getattr(widget, "section_name_edit", None)
            if name_field is None:
                name_field = getattr(widget, "name_edit", None)
            if name_field is not None:
                result[name_field.text()] = type(widget).__name__
        return result

    # ── Data API ───────────────────────────────────────────────────────────

    def get_data_values(self, just_data=False):
        data = {}

        # Read connectivity from matrix before building distributor data
        connectivity = self.connection_matrix_frame.get_connectivity()

        distributor_data_list, distributors = self.distributor_frame.get_data_values()
        # Inject connectivity from matrix into each distributor's data dict
        for d_data in distributor_data_list:
            name = d_data.get("distributor name", "")
            if name in connectivity:
                d_data["assigned_propulsors"] = connectivity[name]["assigned_propulsors"]
                d_data["assigned_sources"]    = connectivity[name]["assigned_sources"]
            else:
                d_data.setdefault("assigned_propulsors", [])
                d_data.setdefault("assigned_sources",    [])

        data["distributor data"] = distributor_data_list
        data["source data"],    sources    = self.energy_source_frame.get_data_values()
        data["propulsor data"], propulsors = self.propulsor_frame.get_data_values()
        data["system data"],    systems    = self.system_frame.get_data_values()
        data["converter data"], converters = self.converter_frame.get_data_values()

        if just_data:
            return data

        net = self.create_rcaide_structure(
            data, distributors, sources, propulsors, converters, systems
        )
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
            distributor.assigned_propulsors = [assigned]

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
        self._migrate_connections(data)

        self.distributor_frame.load_data(data.get("distributor data", []))
        self.energy_source_frame.load_data(data.get("source data", []))
        self.propulsor_frame.load_data(data.get("propulsor data", []))
        self.system_frame.load_data(data.get("system data", []))
        converter_data = data.get("converter data", data.get("converter  data", []))
        self.converter_frame.load_data(converter_data)

        # Populate the connection matrix from loaded data
        self._refresh_matrix()

    @staticmethod
    def _migrate_connections(data):
        """Convert old connections-matrix format into assigned_propulsors/assigned_sources."""
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
