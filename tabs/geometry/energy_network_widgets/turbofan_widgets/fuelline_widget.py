import os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from utilities import Units
from widgets.unit_picker_widget import UnitPickerWidget
from tabs.geometry.energy_network_widgets.turbofan_widgets.propulsors_widget import PropulsorWidget
from tabs.geometry.energy_network_widgets.turbofan_widgets.fuel_tanks_widget import FuelTankWidget

class FuelLineWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None):
        super().__init__()

        self.index = index
        self.on_delete = on_delete
        self.data_fields = {}
        self.init_ui(section_data)

    def init_ui(self, section_data):
        main_layout = QVBoxLayout(self)

        # Segment Name layout
        self.name_layout = QHBoxLayout()
        self.name_layout.addWidget(QLabel("Fuel Line Name: "))
        self.name_edit = QLineEdit()
        self.name_layout.addWidget(self.name_edit)
        main_layout.addLayout(self.name_layout)

        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create Fuel Tanks tab
        fuel_tank_widget = FuelTankWidget(self.index, self.on_delete, section_data)
        self.tab_widget.addTab(fuel_tank_widget, "Fuel Tanks")

        # Create Propulsors tab
        propulsor_widget = PropulsorWidget(self.index, self.on_delete, section_data)
        self.tab_widget.addTab(propulsor_widget, "Propulsors")


        if section_data:
            self.load_data_values(section_data)

    def get_data_values(self):
        data = {}
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value = float(line_edit.text()) if line_edit.text() else 0.0
            data[label] = unit_picker.apply_unit(value), unit_picker.current_index

        data["segment name"] = self.name_edit.text()
        print("Data Values:", data)
        return data

    def load_data_values(self, section_data):
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value, index = section_data[label]
            line_edit.setText(str(value))
            unit_picker.set_index(index)

        self.name_edit.setText(section_data["segment name"])

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)