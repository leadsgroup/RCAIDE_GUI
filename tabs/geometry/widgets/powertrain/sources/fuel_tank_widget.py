# RCAIDE_GUI/tabs/geometry/widgets/powertrain/sources/fuel_tank_widget.py

# Created: Dec 2025, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFrame,
    QSizePolicy, QComboBox, QCheckBox,
)
from PyQt6.QtCore import Qt

from tabs.geometry.widgets import GeometryDataWidget
from utilities import Units
from common_widgets import DataEntryWidget


# ------------------------------------------------------------------------------
#  Fuel Tank Widget
# ------------------------------------------------------------------------------
class FuelTankWidget(GeometryDataWidget):

    TANK_TYPES   = ['Fuel Tank', 'Non-Integral Tank', 'Integral Tank', 'Cryogenic Tank']
    FUEL_TYPES   = ['Jet A1', 'Jet A', 'JP7', 'Aviation Gasoline',
                    'Liquid Hydrogen', 'Liquid Natural Gas']
    GEOMETRY_TYPES = ['cylindrical', 'conformal', 'prismatic']

    _TANK_CLASS = {
        'Fuel Tank':         lambda: RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Fuel_Tank(),
        'Non-Integral Tank': lambda: RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Non_Integral_Tank(),
        'Integral Tank':     lambda: RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Integral_Tank(),
        'Cryogenic Tank':    lambda: RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Cryogenic_Tank(),
    }

    _FUEL_CLASS = {
        'Jet A1':             lambda: RCAIDE.Library.Attributes.Propellants.Jet_A1(),
        'Jet A':              lambda: RCAIDE.Library.Attributes.Propellants.Jet_A(),
        'JP7':                lambda: RCAIDE.Library.Attributes.Propellants.JP7(),
        'Aviation Gasoline':  lambda: RCAIDE.Library.Attributes.Propellants.Aviation_Gasoline(),
        'Liquid Hydrogen':    lambda: RCAIDE.Library.Attributes.Propellants.Liquid_Hydrogen(),
        'Liquid Natural Gas': lambda: RCAIDE.Library.Attributes.Propellants.Liquid_Natural_Gas(),
    }

    def __init__(self, index, on_delete, data_values=None):
        super().__init__()
        self.index     = index
        self.on_delete = on_delete

        layout = QVBoxLayout()
        layout.setSpacing(4)

        # --- Name ---
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Fuel Tank Name:"))
        self.section_name_edit = QLineEdit()
        name_row.addWidget(self.section_name_edit)
        layout.addLayout(name_row)

        # --- Tank type / Fuel type ---
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Tank Type:"))
        self.tank_type_combo = QComboBox()
        self.tank_type_combo.addItems(self.TANK_TYPES)
        self.tank_type_combo.setFixedWidth(200)
        type_row.addWidget(self.tank_type_combo)

        type_row.addSpacing(20)
        type_row.addWidget(QLabel("Fuel Type:"))
        self.fuel_type_combo = QComboBox()
        self.fuel_type_combo.addItems(self.FUEL_TYPES)
        self.fuel_type_combo.setFixedWidth(200)
        type_row.addWidget(self.fuel_type_combo)
        type_row.addStretch(1)
        layout.addLayout(type_row)

        # --- Basic fields ---
        basic_labels = [
            ("Fuel Tank Origin", Units.Position),
            ("Fuel Origin",      Units.Position),
            ("Center of Gravity",Units.Position),
            ("Mass",             Units.Mass),
            ("Internal Volume",  Units.Volume),
        ]
        self.basic_widget = DataEntryWidget(basic_labels)
        layout.addWidget(self.basic_widget)

        # --- Wing / geometry section ---
        wing_row = QHBoxLayout()
        wing_row.addWidget(QLabel("Wing Tag:"))
        self.wing_tag_edit = QLineEdit()
        self.wing_tag_edit.setFixedWidth(200)
        wing_row.addWidget(self.wing_tag_edit)

        wing_row.addSpacing(20)
        wing_row.addWidget(QLabel("Geometry Type:"))
        self.geometry_combo = QComboBox()
        self.geometry_combo.addItems(self.GEOMETRY_TYPES)
        self.geometry_combo.setFixedWidth(160)
        wing_row.addWidget(self.geometry_combo)

        wing_row.addSpacing(20)
        self.transverse_check = QCheckBox("Transverse Tank")
        wing_row.addWidget(self.transverse_check)
        wing_row.addStretch(1)
        layout.addLayout(wing_row)

        # --- Dimension fields ---
        dim_labels = [
            ("External Length",   Units.Length),
            ("External Width",    Units.Length),
            ("External Height",   Units.Length),
            ("External Diameter", Units.Length),
        ]
        self.dim_widget = DataEntryWidget(dim_labels)
        layout.addWidget(self.dim_widget)

        # --- Cryogenic-specific fields ---
        self.cryo_label = QLabel("<b>Cryogenic Parameters</b>")
        layout.addWidget(self.cryo_label)
        cryo_labels = [
            ("Design Altitude",          Units.Length),
            ("Design Inlet Temperature", Units.Temperature),
            ("Ullage Volume Fraction",   Units.Unitless),
            ("Safety Factor",            Units.Unitless),
            ("Pressure Factor",          Units.Unitless),
            ("Accessories Weight Factor",Units.Unitless),
        ]
        self.cryo_widget = DataEntryWidget(cryo_labels)
        layout.addWidget(self.cryo_widget)

        # Delete button
        delete_btn = QPushButton("Delete Fuel Tank")
        delete_btn.clicked.connect(self.delete_button_pressed)
        layout.addWidget(delete_btn)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.tank_type_combo.currentTextChanged.connect(self._update_cryo_visibility)
        self._update_cryo_visibility(self.tank_type_combo.currentText())

        if data_values:
            self.load_data_values(data_values)

    def _update_cryo_visibility(self, tank_type):
        is_cryo = (tank_type == 'Cryogenic Tank')
        self.cryo_label.setVisible(is_cryo)
        self.cryo_widget.setVisible(is_cryo)

    def delete_button_pressed(self):
        if self.on_delete is None:
            return
        self.on_delete(self.index)

    def load_data_values(self, data):
        self.section_name_edit.setText(data.get('Source Name', ''))

        tank_type = data.get('tank_type', 'Fuel Tank')
        idx = self.tank_type_combo.findText(tank_type)
        if idx >= 0:
            self.tank_type_combo.setCurrentIndex(idx)

        fuel_type = data.get('fuel_type', 'Jet A1')
        idx = self.fuel_type_combo.findText(fuel_type)
        if idx >= 0:
            self.fuel_type_combo.setCurrentIndex(idx)

        self.basic_widget.load_data(data)
        self.dim_widget.load_data(data)
        self.cryo_widget.load_data(data)

        self.wing_tag_edit.setText(data.get('wing_tag', '') or '')

        geom = data.get('geometry_type', 'cylindrical')
        idx = self.geometry_combo.findText(geom)
        if idx >= 0:
            self.geometry_combo.setCurrentIndex(idx)

        transverse = data.get('transverse_tank', [False, 0])
        val = transverse[0] if isinstance(transverse, (list, tuple)) else transverse
        self.transverse_check.setChecked(bool(val))

        self._update_cryo_visibility(self.tank_type_combo.currentText())

    def get_data_values(self):
        data    = {}
        data_si = {}

        data.update(self.basic_widget.get_values())
        data_si.update(self.basic_widget.get_values_si())
        data.update(self.dim_widget.get_values())
        data_si.update(self.dim_widget.get_values_si())
        data.update(self.cryo_widget.get_values())
        data_si.update(self.cryo_widget.get_values_si())

        name      = self.section_name_edit.text()
        tank_type = self.tank_type_combo.currentText()
        fuel_type = self.fuel_type_combo.currentText()
        wing_tag  = self.wing_tag_edit.text().strip()
        geom_type = self.geometry_combo.currentText()
        transverse= self.transverse_check.isChecked()

        for d in (data, data_si):
            d['Source Name']   = name
            d['source_type']   = 'Fuel Tank'
            d['tank_type']     = tank_type
            d['fuel_type']     = fuel_type
            d['wing_tag']      = wing_tag
            d['geometry_type'] = geom_type
            d['transverse_tank'] = [transverse, 0]

        return data, self.create_rcaide_structure(data_si)

    def create_rcaide_structure(self, data):
        name      = data.get('Source Name', '')
        tank_type = data.get('tank_type', 'Fuel Tank')
        fuel_type = data.get('fuel_type', 'Jet A1')

        tank_factory = self._TANK_CLASS.get(tank_type, self._TANK_CLASS['Fuel Tank'])
        tank = tank_factory()
        tank.tag = name

        origin = data.get('Fuel Tank Origin', [[0, 0, 0]])
        tank.origin = origin[0] if isinstance(origin, (list, tuple)) else origin

        wing_tag = data.get('wing_tag', '') or ''
        if wing_tag:
            tank.wing_tag = wing_tag

        tank.transverse_tank = bool(
            data.get('transverse_tank', [False])[0]
            if isinstance(data.get('transverse_tank'), (list, tuple))
            else data.get('transverse_tank', False)
        )

        if hasattr(tank, 'geometry_type'):
            tank.geometry_type = data.get('geometry_type', 'cylindrical')

        def _first(v):
            return v[0] if isinstance(v, (list, tuple)) else v

        tank.lengths.external   = _first(data.get('External Length',   [0, 0]))
        tank.widths.external    = _first(data.get('External Width',     [0, 0]))
        tank.heights.external   = _first(data.get('External Height',    [0, 0]))
        tank.diameters.external = _first(data.get('External Diameter',  [0, 0]))

        if tank_type == 'Cryogenic Tank':
            tank.design_altitude               = _first(data.get('Design Altitude',           [0, 0]))
            tank.design_inlet_temperature      = _first(data.get('Design Inlet Temperature',  [20, 0]))
            tank.ullage_volume_fraction        = _first(data.get('Ullage Volume Fraction',    [0.07, 0]))
            tank.safety_factor                 = _first(data.get('Safety Factor',             [1.6, 0]))
            tank.pressure_factor               = _first(data.get('Pressure Factor',           [5, 0]))
            tank.tank_accesories_weight_factor = _first(data.get('Accessories Weight Factor', [1.5, 0]))

        fuel_factory = self._FUEL_CLASS.get(fuel_type, self._FUEL_CLASS['Jet A1'])
        fuel = fuel_factory()

        fuel_origin = data.get('Fuel Origin', [[0, 0, 0]])
        fuel.origin = fuel_origin[0] if isinstance(fuel_origin, (list, tuple)) else fuel_origin

        cg = data.get('Center of Gravity', [[0, 0, 0]])
        fuel.mass_properties.center_of_gravity = cg[0] if isinstance(cg, (list, tuple)) else cg
        fuel.mass_properties.mass = _first(data.get('Mass', [0, 0]))

        vol = _first(data.get('Internal Volume', [0, 0]))
        fuel.volume_properties.net_volume = vol

        tank.fuel = fuel
        return tank
