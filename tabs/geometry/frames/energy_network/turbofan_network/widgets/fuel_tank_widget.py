import RCAIDE
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFrame

from tabs.geometry.frames import GeometryFrame
from utilities import Units
from widgets import DataEntryWidget


class FuelTankWidget(QWidget, GeometryFrame):
    def __init__(self, index, on_delete, data_values=None):
        super(FuelTankWidget, self).__init__()

        self.data_values = {}
        self.index = index
        self.on_delete = on_delete

        main_section_layout = QVBoxLayout()

        data_units_labels = [
            ("Fuel Tank Origin", Units.Position),
            ("Fuel", Units.Heading),
            ("Fuel Origin", Units.Position),
            ("Center of Gravity", Units.Position),
            ("Fuel", Units.Unitless),
            ("Mass", Units.Mass),
            ("Internal Volume", Units.Volume),
        ]

        self.name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        self.name_layout.addWidget(QLabel("Fuel Tank Name: "))
        self.name_layout.addWidget(self.section_name_edit)
        main_section_layout.addLayout(self.name_layout)

        self.data_entry_widget = DataEntryWidget(data_units_labels)
        main_section_layout.addWidget(self.data_entry_widget)

        delete_button = QPushButton("Delete Fuel Tank", self)
        delete_button.clicked.connect(self.delete_button_pressed)

        main_section_layout.addWidget(delete_button)

        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        main_section_layout.addWidget(line_bar)

        self.setLayout(main_section_layout)

        if data_values:
            self.load_data_values(data_values)

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)

    def load_data_values(self, section_data):
        self.data_entry_widget.load_data(section_data)
        self.section_name_edit.setText(section_data["segment name"])

    def get_data_values(self):
        title = self.section_name_edit.text()
        data = self.data_entry_widget.get_values()
        data["segment name"] = title

        data_si = self.data_entry_widget.get_values_si()
        data_si["segment name"] = title

        return data, self.create_rcaide_structure(data_si)

    def create_rcaide_structure(self, data):
        fuel_tank = RCAIDE.Library.Components.Energy.Fuel_Tanks.Fuel_Tank()
        fuel_tank.tag = data["segment name"]
        fuel_tank.origin = data["Fuel Tank Origin"][0]

        fuel = RCAIDE.Library.Attributes.Propellants.Aviation_Gasoline()
        fuel.mass_properties.mass = data["Mass"][0]
        fuel.origin = data["Fuel Origin"][0]
        fuel.mass_properties.center_of_gravity = data["Center of Gravity"][0]
        fuel.internal_volume = data["Internal Volume"][0]
        fuel_tank.fuel = fuel

        return fuel_tank
