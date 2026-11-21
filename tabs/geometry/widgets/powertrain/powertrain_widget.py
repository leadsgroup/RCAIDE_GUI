# RCAIDE_GUI/tabs/geometry/widgets/powertrain/powertrain_widget.py

# Created: Dec 2025, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE

_Battery_Pack = RCAIDE.Library.Components.Powertrain.Sources.Batteries.Battery_Pack
_Coolant_Line = RCAIDE.Library.Components.Powertrain.Distributors.Coolant_Line
_Converter    = RCAIDE.Library.Components.Powertrain.Converters.Converter

_NETWORK_CLASS_MAP = {
    "Fuel":      RCAIDE.Framework.Networks.Fuel,
    "Electric":  RCAIDE.Framework.Networks.Electric,
    "Hybrid":    RCAIDE.Framework.Networks.Hybrid,
    "Hydrogen":  RCAIDE.Framework.Networks.Hydrogen,
    "Fuel Cell": RCAIDE.Framework.Networks.Fuel_Cell,
}

from RCAIDE.Framework.Core import Data
from utilities import BTN_STYLE, CONNECTION_GROUPS, empty_connections, set_data


def nested_converter_paths(component, prefix=""):
    """Yield (dotted path, converter) for every converter nested inside an RCAIDE component."""
    for key, value in component.items():
        if not isinstance(value, Data):
            continue
        path = prefix + key
        if isinstance(value, _Converter):
            yield path, value
        yield from nested_converter_paths(value, path + ".")


def share_nested_converters(propulsors, converters):
    """Put each network converter that also sits inside a propulsor (e.g. a compressor motor) back into that propulsor, so both refer to one object."""
    converter_by_tag = {converter.tag: converter for converter in converters}
    for propulsor in propulsors:
        for path, nested in list(nested_converter_paths(propulsor)):
            if nested.tag in converter_by_tag:
                set_data(propulsor, path, converter_by_tag[nested.tag])


def assign_distributors(component, distributor_tags):
    """Set RCAIDE ``assigned_distributors`` from a list of distributor tags (None when unconnected)."""
    component.assigned_distributors = [list(distributor_tags)] if distributor_tags else None

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

    Contains sub-tabs for Distributors, Propulsors, Energy Sources, Systems,
    Converters, Connections and the Network Diagram.  The Connections tab shows
    a matrix of propulsors, sources, converters and systems against
    distributors so that many-to-many connectivity is edited in one place.

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
        component_names = {
            "assigned_propulsors": self._collect_names(self.propulsor_frame.propulsor_sections_layout),
            "assigned_sources":    self._collect_names(self.energy_source_frame.source_sections_layout),
            "assigned_converters": self._collect_names(self.converter_frame.converter_sections_layout),
            "assigned_systems":    self._collect_names(self.system_frame.systems_layout),
        }
        distributor_names, connectivity = self._collect_distributor_info()

        # Preserve each component's concrete editor type so the diagram can
        # distinguish components that share the same broad powertrain group.
        component_types = {}
        component_types.update(self._collect_types(self.energy_source_frame.source_sections_layout))
        component_types.update(self._collect_types(self.distributor_frame.distributor_sections_layout))
        component_types.update(self._collect_types(self.propulsor_frame.propulsor_sections_layout))

        # Keep the editable matrix and its visual representation synchronized
        # from one snapshot of the current component names and connections.
        self.connection_matrix_frame.refresh(component_names, distributor_names, connectivity)
        self.powertrain_diagram.refresh(
            component_names["assigned_propulsors"], component_names["assigned_sources"],
            distributor_names, connectivity,
            component_names["assigned_converters"], component_names["assigned_systems"],
            component_types,
        )

    def _collect_distributor_info(self) -> tuple[list[str], dict]:
        """Return (ordered list of distributor names, connectivity dict).

        connectivity[dist_name] holds one list of connected component names
        per key in ``CONNECTION_GROUPS``.
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
            # Connectivity stored during load_data_values (empty for new widgets)
            connectivity[name] = {key: list(widget.loaded_connections.get(key, [])) for key, _ in CONNECTION_GROUPS}
        return names, connectivity

    @staticmethod
    def _name_field(widget):
        """Return the name QLineEdit for a component editor widget, or None.

        Most editors expose ``section_name_edit``; a few use ``name_edit``.
        """
        return getattr(widget, "section_name_edit", None) or getattr(widget, "name_edit", None)

    @staticmethod
    def _collect_names(layout) -> list[str]:
        """Return displayed names for all component editors in a layout."""
        names = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is None:
                continue
            field = PowertrainWidget._name_field(widget)
            if field is not None:
                names.append(field.text())
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
            field = PowertrainWidget._name_field(widget)
            if field is not None:
                result[field.text()] = type(widget).__name__
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
            d_data.update(connectivity.get(name, empty_connections()))

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
        """Build the RCAIDE network: every component lists the tags of the distributors it connects to."""
        net_class = _NETWORK_CLASS_MAP.get(self.network_type, RCAIDE.Framework.Networks.Fuel)
        net = net_class()

        # Invert the per-distributor connectivity into per-component distributor tags
        distributor_tags = {key: {} for key, _ in CONNECTION_GROUPS}
        for d_data, distributor in zip(data.get("distributor data", []), distributors):
            for key, _ in CONNECTION_GROUPS:
                for name in d_data.get(key, []):
                    distributor_tags[key].setdefault(name, []).append(distributor.tag)
            net.distributors.append(distributor)

        coolant_tags = {d.tag for d in distributors if isinstance(d, _Coolant_Line)}
        share_nested_converters(propulsors, converters)

        groups = [
            ("assigned_propulsors", propulsors, net.propulsors),
            ("assigned_sources",    sources,    net.sources),
            ("assigned_converters", converters, net.converters),
            ("assigned_systems",    systems,    net.systems),
        ]
        for key, components, container in groups:
            for component in components:
                tags = distributor_tags[key].get(component.tag, [])
                if isinstance(component, _Battery_Pack):
                    # The pack feeds electrical buses; its modules are cooled by coolant lines
                    assign_distributors(component, [t for t in tags if t not in coolant_tags])
                    for module in component.modules:
                        assign_distributors(module, [t for t in tags if t in coolant_tags])
                else:
                    assign_distributors(component, tags)
                container.append(component)

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
