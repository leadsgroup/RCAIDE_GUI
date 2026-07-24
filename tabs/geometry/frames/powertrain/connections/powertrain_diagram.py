"""Build and display an engineering-style SVG powertrain schematic.

Component names and connection assignments come from the powertrain editor.
This module lays them out in functional columns, creates one SVG document in
memory, and displays it with Qt without writing a temporary diagram file.
"""

from html import escape
from pathlib import Path
import os
import re

from utilities import APP_DATA

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

# Resolve the reusable pictograph library via the installed app_data package.
_SYMBOL_DIR = Path(os.path.join(APP_DATA, "images", "powertrain_symbols"))

# Cache parsed fragments because the same icon may appear several times.
_SYMBOL_CACHE: dict[str, str] = {}


_SYMBOL_PLACEHOLDER = (
    '<rect x="1" y="1" width="54" height="56" fill="#eaf2f8" '
    'stroke="#526d82" stroke-width="1.5"/>'
)


def _svg_symbol(filename):
    """Return an icon fragment fitted into a 56 by 58 diagram cell.

    Qt supports SVG Tiny and ignores SVG documents nested inside another SVG.
    The asset root is therefore removed and its body is wrapped in a scaled
    ``<g>`` element instead.  Returns a grey placeholder rectangle if the
    asset is missing or malformed so one bad file cannot crash the diagram.
    """
    if filename not in _SYMBOL_CACHE:
        try:
            # Read the source coordinate system and markup inside its root element.
            source = (_SYMBOL_DIR / filename).read_text(encoding="utf-8")
            view_box = re.search(r'viewBox="([^"]+)"', source)
            body = re.search(r"<svg\b[^>]*>(.*)</svg>\s*$", source, re.DOTALL)
            if view_box is None or body is None:
                raise ValueError(f"Missing viewBox or body in {filename}")
            vals = view_box.group(1).split()
            if len(vals) != 4:
                raise ValueError(f"Expected 4 viewBox values in {filename}, got {len(vals)}")
            _, _, source_w, source_h = (float(v) for v in vals)
            # Scale uniformly, then center the unused space on both sides.
            scale = min(54.0 / source_w, 56.0 / source_h)
            offset_x = 1.0 + (54.0 - source_w * scale) / 2.0
            offset_y = 1.0 + (56.0 - source_h * scale) / 2.0
            _SYMBOL_CACHE[filename] = (
                f'<g transform="translate({offset_x:.3f} {offset_y:.3f}) '
                f'scale({scale:.6f})">{body.group(1)}</g>'
            )
        except Exception:
            _SYMBOL_CACHE[filename] = _SYMBOL_PLACEHOLDER
    return _SYMBOL_CACHE[filename]


class PowertrainDiagramWidget(QWidget):
    """Display the current network as a scrollable engineering drawing."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        # This hint is shown only while the network has no components.
        self._hint = QLabel(
            "Add components, assign their connections, then refresh the schematic."
        )
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setStyleSheet("color: grey; font-style: italic; padding: 16px;")

        # Keep a fixed drawing size inside the scroll area. Allowing the scroll
        # area to resize this widget would stretch the schematic unevenly.
        self._svg = QSvgWidget()
        self._svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self._svg.setMinimumSize(900, 520)
        self._svg.resize(1200, 680)

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)  # prevents non-uniform SVG distortion
        scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._svg)
        layout.addWidget(self._hint)
        layout.addWidget(scroll, 1)

    def refresh(self, propulsors, sources, distributors, connectivity,
                converters=None, systems=None, component_types=None):
        """Regenerate the drawing from the latest powertrain editor state.

        ``connectivity`` maps distributor names to assigned source and
        propulsor name lists. ``component_types`` maps display names to their
        concrete editor widget classes for pictograph selection.
        """
        converters = converters or []
        systems = systems or []
        has_nodes = bool(sources or distributors or propulsors or converters or systems)
        self._hint.setVisible(not has_nodes)
        self._svg.setVisible(has_nodes)
        if not has_nodes:
            return
        # SVG construction is independent from Qt so it can be tested directly.
        svg, width, height = self._build_svg(
            propulsors, sources, distributors, connectivity, converters, systems,
            component_types,
        )
        self._svg.setFixedSize(width, height)
        self._svg.load(QByteArray(svg.encode("utf-8")))

    @staticmethod
    def _build_svg(propulsors, sources, distributors, connectivity,
                   converters=None, systems=None, component_types=None):
        """Return the generated SVG markup and its required widget dimensions."""
        converters, systems = converters or [], systems or []
        component_types = component_types or {}
        # Placeholders preserve the three-column layout for incomplete networks.
        sources = sources or ["UNASSIGNED SOURCE"]
        distributors = distributors or ["UNASSIGNED DISTRIBUTOR"]
        propulsors = propulsors or ["UNASSIGNED PROPULSOR"]

        # Drawing geometry — all values are SVG user units (= screen pixels at 1×).
        width = 1200
        row_gap, box_w, box_h = 108, 210, 58   # row pitch, source card width/height
        dist_box_w = 300                         # wider cards for distribution column
        prop_box_w = 300                         # wider cards for propulsion column
        top = 145                                # y-coordinate of first component row
        main_rows = max(len(sources), len(distributors), len(propulsors))
        # Auxiliary equipment is packed into three columns below the main flow.
        aux_items = (
            [(name, "CNV") for name in converters]
            + [(name, "SYS") for name in systems]
        )
        aux_rows = max(1, (len(aux_items) + 2) // 3)
        aux_top = top + main_rows * row_gap + 48
        height = max(560, aux_top + aux_rows * 66 + 76)
        xs = (150, 570, 990)

        def y_for(items, name):
            """Find the top coordinate of a named component's row."""
            return top + items.index(name) * row_gap

        def safe(value):
            """Escape user text for XML and shorten it to fit a card."""
            value = str(value)
            return escape(value if len(value) <= 24 else value[:22] + "…")

        # Accumulate fragments and join once instead of repeatedly copying one
        # increasingly large SVG string.
        parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMin meet">
<defs>
 <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#17324d"/></marker>
</defs>
<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>
<rect x="18" y="18" width="1164" height="{height-36}" fill="#ffffff" stroke="#17324d" stroke-width="2"/>
<path d="M18 82H1182" stroke="#17324d" stroke-width="2"/>
<text x="38" y="51" font-family="Arial,sans-serif" font-size="22" font-weight="700" fill="#102a43">POWERTRAIN NETWORK SCHEMATIC</text>
<text x="38" y="70" font-family="Arial,sans-serif" font-size="11" fill="#486581">RCAIDE · ENERGY FLOW AND COMPONENT CONNECTIVITY</text>
<text x="1138" y="51" text-anchor="end" font-family="Arial,sans-serif" font-size="10" fill="#486581">DWG: PTN-001</text>
<rect x="40" y="91" width="220" height="31" fill="#eaf2f8"/>
<rect x="420" y="91" width="300" height="31" fill="#eaf2f8"/>
<rect x="840" y="91" width="300" height="31" fill="#eaf2f8"/>
<text x="150" y="111" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#102a43">ENERGY SOURCE</text>
<text x="570" y="111" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#102a43">DISTRIBUTION</text>
<text x="990" y="111" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#102a43">PROPULSION / LOAD</text>
<path d="M282 92V{aux_top-20}M757 92V{aux_top-20}" stroke="#9fb3c8" stroke-width="1" stroke-dasharray="5 5"/>''']

        # Draw orthogonal energy paths behind the equipment symbols.
        for dist in distributors:
            dist_y = y_for(distributors, dist) + box_h / 2
            connected_sources = connectivity.get(dist, {}).get("assigned_sources", [])
            connected_props = connectivity.get(dist, {}).get("assigned_propulsors", [])
            for src in connected_sources:
                if src in sources:
                    sy = y_for(sources, src) + box_h / 2
                    parts.append(f'<path d="M255 {sy}H330V{dist_y}H420" fill="none" stroke="#17324d" stroke-width="2.5" marker-end="url(#arrow)"/>')
            for prop in connected_props:
                if prop in propulsors:
                    py = y_for(propulsors, prop) + box_h / 2
                    parts.append(f'<path d="M720 {dist_y}H760V{py}H840" fill="none" stroke="#17324d" stroke-width="2.5" marker-end="url(#arrow)"/>')

        def pictograph(name, kind):
            """Select a supplied pictograph using component type and name.

            The widget class is the primary signal. Including the display name
            provides a fallback for older saved data with incomplete type data.
            """
            widget_type = component_types.get(name, "")
            key = (widget_type + " " + str(name)).lower()
            if kind == "source" and "battery" in key:
                return _svg_symbol("battery.svg")
            if kind == "source":  # AIAA fuel-tank pictograph
                return _svg_symbol("fuel_tank.svg")
            if kind == "distribution" and "electricalbus" in key:
                return _svg_symbol("electrical_bus.svg")
            if kind == "distribution" and "coolant" in key:
                return _svg_symbol("cooler_passive.svg")
            if kind == "distribution":  # transmission/routing node
                return _svg_symbol("electrical_transmission_routing_node.svg")
            if "turbofan" in key:
                return _svg_symbol("turbofan_engine.svg")
            if "turbojet" in key or "turboprop" in key:
                return _svg_symbol("turboshaft_engine.svg")
            if "icewidget" in key or "combustion" in key:
                return _svg_symbol("piston_engine.svg")
            # AIAA forward-facing propeller pictograph.
            return _svg_symbol("forward_facing_propeller_clockwise_rotation.svg")

        def symbol_card(x, y, name, kind, ref, card_width=box_w):
            """Create one labeled primary-equipment card and its icon cell."""
            icon = pictograph(name, kind)
            max_chars = 34 if card_width >= 300 else 24
            label = escape(str(name) if len(str(name)) <= max_chars
                           else str(name)[:max_chars - 2] + "…")
            return f'''<g transform="translate({x-card_width/2} {y})">
 <rect width="{card_width}" height="{box_h}" rx="3" fill="#fff" stroke="#17324d" stroke-width="2"/>
 <rect width="58" height="{box_h}" fill="#eaf2f8" stroke="#17324d" stroke-width="2"/>
 <g transform="translate(1 0)" fill="none" stroke="#111111" stroke-width="1.8" stroke-linejoin="round">{icon}</g>
 <text x="69" y="24" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#102a43">{label}</text>
 <text x="69" y="43" font-family="Arial,sans-serif" font-size="9.5" fill="#486581">{ref}</text>
</g>'''

        # Cards are appended after connection paths, placing their opaque
        # backgrounds over the path endpoints.
        for i, name in enumerate(sources):
            parts.append(symbol_card(xs[0], top + i * row_gap, name, "source", f"SRC-{i+1:02d}"))
        for i, name in enumerate(distributors):
            parts.append(symbol_card(
                xs[1], top + i * row_gap, name, "distribution",
                f"DST-{i+1:02d}", dist_box_w,
            ))
        for i, name in enumerate(propulsors):
            parts.append(symbol_card(
                xs[2], top + i * row_gap, name, "propulsor",
                f"PRP-{i+1:02d}", prop_box_w,
            ))

        # Auxiliary equipment is intentionally separated from the primary energy path.
        parts.append(f'<path d="M38 {aux_top-20}H1162" stroke="#17324d" stroke-width="1.5"/><rect x="38" y="{aux_top-14}" width="250" height="27" fill="#eaf2f8"/><text x="49" y="{aux_top+5}" font-family="Arial,sans-serif" font-size="12" font-weight="700" fill="#102a43">AUXILIARY EQUIPMENT / CONTROL</text>')
        for i, (name, prefix) in enumerate(aux_items):
            # Modulo selects a column; integer division advances to the next row.
            col, row = i % 3, i // 3
            x, y = 48 + col * 380, aux_top + 25 + row * 66
            label = safe(name)
            key = str(name).lower()
            # Choose the standardized load pictograph from the system name.
            if "hydraulic" in key:
                load_mark = _svg_symbol("load_hydraulic.svg")
            elif any(word in key for word in ("environment", "pneumatic", "air")):
                load_mark = _svg_symbol("load_pneumatic.svg")
            elif "electrical" in key or "avionics" in key or "instrument" in key:
                load_mark = _svg_symbol("load_electrical.svg")
            else:
                load_mark = _svg_symbol("load_mechanical.svg")
            parts.append(f'<g transform="translate({x} {y})"><rect width="344" height="46" fill="#f8fafc" stroke="#526d82" stroke-width="1.5"/><g transform="scale(.72)">{load_mark}</g><text x="49" y="21" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#102a43">{label}</text><text x="49" y="36" font-family="Arial,sans-serif" font-size="9.5" fill="#486581">{prefix}-{i+1:02d}</text></g>')

        # The bottom strip is reserved for the line-style legend.
        parts.append(f'''<g transform="translate(38 {height-58})">
 <text y="0" font-family="Arial,sans-serif" font-size="9" font-weight="700" fill="#102a43">LEGEND</text>
 <path d="M60 -4h55" stroke="#17324d" stroke-width="2.5" marker-end="url(#arrow)"/><text x="125" y="0" font-family="Arial,sans-serif" font-size="9" fill="#486581">assigned energy flow</text>
 <path d="M265 -4h55" stroke="#9fb3c8" stroke-dasharray="5 5"/><text x="330" y="0" font-family="Arial,sans-serif" font-size="9" fill="#486581">functional boundary</text>
</g></svg>''')
        return "".join(parts), width, height
