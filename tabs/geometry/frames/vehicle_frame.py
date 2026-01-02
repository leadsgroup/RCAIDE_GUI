from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy

from tabs.geometry.frames import GeometryFrame
from utilities import create_line_bar, Units, create_scroll_area
from widgets import DataEntryWidget
import values


class VehicleFrame(GeometryFrame):
    data_units_labels = [
        ("General", Units.Heading),
        ("Reference Area", Units.Area, "reference_area"),
        ("Passengers", Units.Count, "number_of_passengers"),
        ("Max Takeoff Weight", Units.Mass, "mass_properties.max_takeoff"),
        ("Takeoff Weight", Units.Mass, "mass_properties.takeoff"),
        ("Operating Empty Weight", Units.Mass, "mass_properties.operating_empty"),
        ("Max Fuel Weight", Units.Mass, "mass_properties.max_fuel"),
        ("Maximum Zero Fuel Weight", Units.Mass, "mass_properties.max_zero_fuel"),
        ("Fuel Weight", Units.Mass, "mass_properties.fuel"),
        ("Maximum Payload Weight", Units.Mass, "mass_properties.max_payload"),
        ("Payload Weight", Units.Mass, "mass_properties.payload"),
        ("Maximum Landing Weight", Units.Mass, "mass_properties.max_landing"),
        ("Landing Weight", Units.Mass, "mass_properties.landing"),
        ("Flight Envelope", Units.Heading),
        ("Cargo Weight", Units.Mass, "mass_properties.cargo"),
        ("Center of Gravity", Units.Position, "mass_properties.center_of_gravity"),
        ("Moment of Intertia", Units.Intertia,
         "mass_properties.moments_of_inertia.tensor"),
        ("Ultimate Load", Units.Unitless, "flight_envelope.ultimate_load"),
        ("Positive Limit Load", Units.Unitless,
         "flight_envelope.positive_limit_load"),
        ("Negative Limit Load", Units.Unitless,
         "flight_envelope.negative_limit_load"),
        ("Systems", Units.Heading),
        ("Design Cruise Altitude", Units.Length,
         "flight_envelope.design_cruise_altitude"),
        ("Design Range", Units.Length, "flight_envelope.design_range"),
        ("Aircraft Category", Units.Unitless, "flight_envelope.category"),
        ("FAR Part Classification Number", Units.Unitless,
         "flight_envelope.FAR_part_number"),
        ("Control Systems", Units.Area, "systems.control"),  # should be drop down
        ("Accessories", Units.Count, "systems.accessories"),  # should be dropdown
    ]

    def __init__(self):
        super().__init__()
        self.data = []
        self.data_entry_widget = None
        self.main_layout = QVBoxLayout()
        create_scroll_area(self)

        self.main_layout.addWidget(QLabel("<b>Vehicle</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.general_data_entry_widget = DataEntryWidget(
            self.data_units_labels)
        self.main_layout.addWidget(self.general_data_entry_widget)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_data)
        self.main_layout.addWidget(save_button)

        self.main_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def load_data(self, data, index):
        self.data = data
        self.index = index

        assert self.name_line_edit is not None
        assert self.data_entry_widget is not None

        self.name_line_edit.setText(data["name"])
        self.data_entry_widget.load_data(data)

    def create_rcaide_structure(self):
        raise NotImplementedError("This method should not be called")

    def get_data_values(self):
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        data = self.data_entry_widget.get_values()
        data["name"] = self.name_line_edit.text()
        return data

    def update_layout(self):
        assert self.data_entry_widget is not None and isinstance(
            self.data_entry_widget, DataEntryWidget)

        if values.geometry_data[0]:
            self.data_entry_widget.load_data(values.geometry_data[0])

    def save_data(self):
        assert self.save_function is not None
        self.save_function(self.tab_index, vehicle_component=None,
                           index=-1, data=self.get_data_values())
