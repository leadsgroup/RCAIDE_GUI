from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy

from tabs.geometry.frames import GeometryFrame
from utilities import create_line_bar, Units, create_scroll_area
from widgets import DataEntryWidget
import values

from widgets.collapsible_section import CollapsibleSection

class VehicleFrame(GeometryFrame):
    data_units_labels = [
        ("Max Takeoff Weight", Units.Mass, "mass_properties.max_takeoff"),
        ("Actual Takeoff Weight", Units.Mass, "mass_properties.takeoff"),
        ("Operating Empty Weight", Units.Mass, "mass_properties.operating_empty"),
        ("Maximum Zero Fuel Weight", Units.Mass, "mass_properties.max_zero_fuel"),
        ("Cargo Weight", Units.Mass, "mass_properties.cargo"),
        ("Ultimate Load", Units.Unitless, "envelope.ultimate_load"),
        ("Limit Load", Units.Unitless, "envelope.limit_load"),
        ("Reference Area", Units.Area, "reference_area"),
        ("Passengers", Units.Count, "passengers"),
    ]

    def __init__(self):
        super().__init__()
        self.data = []
        self.data_entry_widget = None

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        vehicle_content_widget = QWidget()
        self.content_layout = QVBoxLayout(vehicle_content_widget)

        self.name_layout = QHBoxLayout()
        self.name_layout.addWidget(QLabel("Name:"), 3)
        self.name_line_edit = QLineEdit()
        self.name_layout.addWidget(self.name_line_edit, 7)

        self.content_layout.addLayout(self.name_layout)

        self.data_entry_widget = DataEntryWidget(self.data_units_labels)
        self.content_layout.addWidget(self.data_entry_widget)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_data)
        self.content_layout.addWidget(save_button)

        self.content_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        collapsible = CollapsibleSection("Vehicle", vehicle_content_widget)
        main_layout.addWidget(collapsible)

    def load_data(self, data, index):
        self.data = data
        self.index = index

        assert self.name_line_edit is not None
        assert self.data_entry_widget is not None

        self.name_line_edit.setText(data["name"])
        self.data_entry_widget.load_data(data)

    def create_rcaide_structure(self):
        raise NotImplementedError("This method should not be called")
        # vehicle = RCAIDE.Vehicle()
        # vehicle.tag = data["name"]

        # for data_unit_label in self.data_units_labels:
        #     rcaide_label = data_unit_label[-1]
        #     user_label = data_unit_label[0]
        #     set_data(vehicle, rcaide_label, data[user_label][0])

    def get_data_values(self):
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        data = self.data_entry_widget.get_values()
        data["name"] = self.name_line_edit.text()

        # si_data = self.data_entry_widget.get_values_si()
        # si_data["name"] = data["name"]

        # vehicle = self.create_rcaide_structure(si_data)
        return data

    def update_layout(self):
        print("Updating layout")
        assert self.data_entry_widget is not None and isinstance(
            self.data_entry_widget, DataEntryWidget)
        
        if values.geometry_data[0]:
            self.data_entry_widget.load_data(values.geometry_data[0])

    def save_data(self):
        assert self.save_function is not None
        self.save_function(self.tab_index, vehicle_component=None,
                           index=-1, data=self.get_data_values())