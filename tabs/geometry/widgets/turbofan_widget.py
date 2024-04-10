import os
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


from utilities import Units
from widgets.unit_picker_widget import UnitPickerWidget

class FuelTanksWidget(QWidget):
    def __init__(self):
        super(FuelTanksWidget, self).__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Fuel Tanks Widget"))
        self.setLayout(layout)

class PropulsorsWidget(QWidget):
    def __init__(self):
        super(PropulsorsWidget, self).__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Propulsors Widget"))
        self.setLayout(layout)

class TurboFanWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None):
        super(TurboFanWidget, self).__init__()

        main_layout = QVBoxLayout()

        # Dropdown to select number of fuel lines
        self.fuel_lines_label = QLabel("Number of Fuel Lines:")
        self.fuel_lines_combo_box = QComboBox()
        self.fuel_lines_combo_box.addItems(["1", "2", "3", "4"])  # Add more if needed
        self.fuel_lines_combo_box.currentIndexChanged.connect(self.handle_fuel_lines_change)

        main_layout.addWidget(self.fuel_lines_label)
        main_layout.addWidget(self.fuel_lines_combo_box)

        # Tabs for fuel tanks and propulsors
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.handle_tab_change)

        self.fuel_tanks_widget = FuelTanksWidget()
        self.propulsors_widget = PropulsorsWidget()

        self.tabs.addTab(self.fuel_tanks_widget, "Fuel Tanks")
        self.tabs.addTab(self.propulsors_widget, "Propulsors")

        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

    def handle_fuel_lines_change(self, index):
        """Handle change in the number of fuel lines."""
        num_fuel_lines = int(self.fuel_lines_combo_box.currentText())
        # Handle the change, like updating UI based on the number of fuel lines
        pass

    def handle_tab_change(self, index):
        """Handle change in the selected tab."""
        # Handle the change, like updating UI based on the selected tab
        pass
