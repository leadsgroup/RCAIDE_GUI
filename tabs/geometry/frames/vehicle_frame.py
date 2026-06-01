# RCAIDE_GUI/tabs/geometry/frames/vehicle_frame.py
#
# Created:  Dec 2025, M. Clarke

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QComboBox

from tabs.geometry.frames import GeometryFrame
from utilities import create_line_bar, Units, create_scroll_area
from common_widgets import DataEntryWidget
import rcaide_io

_FAR_PARTS   = ["None", "23", "25", "35", "91", "107", "135"]
_CATEGORIES  = ["None", "normal", "utility", "acrobatic", "commuter"]

# Labels that are rendered as standalone QComboBoxes rather than in DataEntryWidget
_COMBO_LABELS = {"FAR Part Classification Number", "Aircraft Category"}


class VehicleFrame(GeometryFrame):
    data_units_labels = [
        # --- General ---
        ("Reference Area",           Units.Area,      "reference_area"),
        ("Passengers",               Units.Count,     "number_of_passengers"),
        # --- Mass Properties ---
        ("Max Takeoff Weight",       Units.Mass,      "mass_properties.max_takeoff"),
        ("Takeoff Weight",           Units.Mass,      "mass_properties.takeoff"),
        ("Operating Empty Weight",   Units.Mass,      "mass_properties.operating_empty"),
        ("Max Fuel Weight",          Units.Mass,      "mass_properties.max_fuel"),
        ("Maximum Zero Fuel Weight", Units.Mass,      "mass_properties.max_zero_fuel"),
        ("Fuel Weight",              Units.Mass,      "mass_properties.fuel"),
        ("Maximum Payload Weight",   Units.Mass,      "mass_properties.max_payload"),
        ("Payload Weight",           Units.Mass,      "mass_properties.payload"),
        ("Maximum Landing Weight",   Units.Mass,      "mass_properties.max_landing"),
        ("Landing Weight",           Units.Mass,      "mass_properties.landing"),
        ("Cargo Weight",             Units.Mass,      "mass_properties.cargo"),
        ("Center of Gravity",        Units.Position,  "mass_properties.center_of_gravity"),
        ("Moment of Intertia",       Units.Intertia,  "mass_properties.moments_of_inertia.tensor"),
        # --- Flight Envelope ---
        ("Ultimate Load",            Units.Unitless,  "flight_envelope.ultimate_load"),
        ("Positive Limit Load",      Units.Unitless,  "flight_envelope.positive_limit_load"),
        ("Negative Limit Load",      Units.Unitless,  "flight_envelope.negative_limit_load"),
        ("Design Dynamic Pressure",  Units.Pressure,  "flight_envelope.design_dynamic_pressure"),
        ("Design Mach Number",       Units.Unitless,  "flight_envelope.design_mach_number"),
        ("Design Cruise Altitude",   Units.Length,    "flight_envelope.design_cruise_altitude"),
        ("Design Range",             Units.Length,    "flight_envelope.design_range"),
        ("V2/VS Ratio",              Units.Unitless,  "flight_envelope.V2_VS_ratio"),
        ("Maximum Lift Coefficient", Units.Unitless,  "flight_envelope.maximum_lift_coefficient"),
        ("Minimum Lift Coefficient", Units.Unitless,  "flight_envelope.minimum_lift_coefficient"),
        # Aircraft Category and FAR Part rendered as QComboBoxes (excluded from DataEntryWidget)
        ("Aircraft Category",        Units.Unitless,  "flight_envelope.category"),
        ("FAR Part Classification Number", Units.Unitless, "flight_envelope.FAR_part_number"),
        # --- Maneuver ---
        ("Maneuver Load Alleviation Factor",  Units.Unitless,  "flight_envelope.maneuver.load_alleviation_factor"),
        ("Maneuver Speed Max Gust",           Units.Velocity,  "flight_envelope.maneuver.equivalent_speed.velocity_max_gust"),
        ("Maneuver Speed Max Cruise",         Units.Velocity,  "flight_envelope.maneuver.equivalent_speed.velocity_max_cruise"),
        ("Maneuver Speed Max Dive",           Units.Velocity,  "flight_envelope.maneuver.equivalent_speed.velocity_max_dive"),
        ("Maneuver Load Factor Max Gust",     Units.Unitless,  "flight_envelope.maneuver.load_factor.velocity_max_gust"),
        ("Maneuver Load Factor Max Cruise",   Units.Unitless,  "flight_envelope.maneuver.load_factor.velocity_max_cruise"),
        ("Maneuver Load Factor Max Dive",     Units.Unitless,  "flight_envelope.maneuver.load_factor.velocity_max_dive"),
        # --- Systems ---
        ("Control Systems",          Units.Unitless,  "systems.control"),
        ("Accessories",              Units.Unitless,  "systems.accessories"),
    ]

    def __init__(self):
        super().__init__()
        self.data = []
        self.data_entry_widget = None
        self.main_layout = QVBoxLayout()
        create_scroll_area(self)

        self.name_line_edit = QLineEdit()

        self.main_layout.addWidget(QLabel("<b>Vehicle</b>"))
        self.main_layout.addWidget(create_line_bar())

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_layout.addWidget(self.name_line_edit)
        self.main_layout.addLayout(name_layout)

        # Numeric / position fields rendered by DataEntryWidget
        widget_labels = [l for l in self.data_units_labels if l[0] not in _COMBO_LABELS]
        self.data_entry_widget = DataEntryWidget(widget_labels)
        self.main_layout.addWidget(self.data_entry_widget)

        # Inject the combo rows directly into DataEntryWidget's QGridLayout so
        # they share its column widths and align perfectly with all other fields.
        # DataEntryWidget uses 4 sub-columns per field: label | input(span 2) | unit-picker
        grid = self.data_entry_widget.layout()
        next_row = grid.rowCount()

        self.category_combo = QComboBox()
        self.category_combo.addItems(_CATEGORIES)
        grid.addWidget(QLabel("Aircraft Category:"), next_row, 0)
        grid.addWidget(self.category_combo, next_row, 1, 1, 2)
        grid.addItem(
            QSpacerItem(80, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum), next_row, 3)

        self.far_combo = QComboBox()
        self.far_combo.addItems(_FAR_PARTS)
        grid.addWidget(QLabel("FAR Part Classification Number:"), next_row, 4)
        grid.addWidget(self.far_combo, next_row, 5, 1, 2)
        grid.addItem(
            QSpacerItem(80, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum), next_row, 7)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_data)
        self.main_layout.addWidget(save_button)

        self.main_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    # ------------------------------------------------------------------
    # Helpers for combo load / save
    # ------------------------------------------------------------------
    @staticmethod
    def _load_combo(combo, raw, choices):
        """Set combo to the string value in raw, falling back to 'None'."""
        val = raw[0] if isinstance(raw, (list, tuple)) else raw
        text = str(val) if val is not None else "None"
        if text in choices:
            combo.setCurrentText(text)
        else:
            combo.setCurrentText("None")

    # ------------------------------------------------------------------
    # GeometryFrame interface
    # ------------------------------------------------------------------
    def load_data(self, data, index):
        self.data  = data
        self.index = index

        self.name_line_edit.setText(data["name"])
        self.data_entry_widget.load_data(data)

        self._load_combo(self.category_combo,
                         data.get("Aircraft Category", [None, 0]),
                         _CATEGORIES)
        self._load_combo(self.far_combo,
                         data.get("FAR Part Classification Number", [None, 0]),
                         _FAR_PARTS)

    def create_rcaide_structure(self):
        raise NotImplementedError("This method should not be called")

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data["name"] = self.name_line_edit.text()

        cat_text = self.category_combo.currentText()
        data["Aircraft Category"] = [None if cat_text == "None" else cat_text, 0]

        far_text = self.far_combo.currentText()
        data["FAR Part Classification Number"] = [None if far_text == "None" else int(far_text), 0]

        return data

    def update_layout(self):
        if isinstance(rcaide_io.rcaide_vehicle, list) and rcaide_io.rcaide_vehicle[0]:
            self.load_data(rcaide_io.rcaide_vehicle[0], 0)

    def save_data(self):
        assert self.save_function is not None
        self.save_function(self.tab_index, vehicle_component=None,
                           index=-1, data=self.get_data_values())
