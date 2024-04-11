import os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from utilities import Units
from widgets.data_entry_widget import DataEntryWidget
from widgets.unit_picker_widget import UnitPickerWidget

class PropulsorWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None):
        super(PropulsorWidget, self).__init__()

        self.data_fields = {}
        self.index = index
        self.on_delete = on_delete
        self.data_entry_widget: DataEntryWidget | None = None

        self.name_layout = QHBoxLayout()  # Corrected the variable name
        self.init_ui(section_data)

    def init_ui(self, section_data):
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()
        # add spacing
        spacer_left = QSpacerItem(80, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(300, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_layout.addItem(spacer_left)
        self.name_line_edit = QLineEdit()  # Define the QLineEdit widget
        self.name_layout.addWidget(QLabel("Segment Name: "))
        self.name_layout.addWidget(self.name_line_edit)
        self.name_layout.addItem(spacer_right)

        main_layout.addLayout(self.name_layout) 

        # List of data labels
        data_units_labels = [
            ("Fan", Units.Unitless),
            ("Working Fluid",Units.Unitless),
            ("Inlet Nozzle", Units.Length),
            ("Low Pressure Compressor", Units.Length),
            ("High Pressure Compressor", Units.Length),
            ("Low Pressure Turbine", Units.Length),
            ("High Pressure Turbine", Units.Length),
            ("Combustor", Units.Length),
            ("Core Nozzle", Units.Length),
            ("Fan Nozzle", Units.Length),
        ]

        self.data_entry_widget = DataEntryWidget(data_units_labels)
        main_layout.addWidget(self.data_entry_widget)
        
        # Add a delete button
        row, col = divmod(len(data_units_labels) + 2, 1)
        delete_button = QPushButton("Delete Section", self)
        delete_button.clicked.connect(self.delete_button_pressed)
        grid_layout.addWidget(delete_button, row, col * 3, 1, 5)

        main_layout.addLayout(grid_layout)

        if section_data: 
            self.load_data_values(section_data)

        self.setLayout(main_layout)


    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        data = self.data_entry_widget.get_values()
        # Retrieve the text from the QLineEdit widget
        data["name"] = self.name_line_edit.text()
        return data


    def load_data_values(self, data, index):
        """Load the data into the widgets.

        Args:
            data: The data to be loaded into the widgets.
            index: The index of the data in the list.
        """
        self.data_entry_widget.load_data(data)

        self.name_line_edit.setText(data["name"])  # Set text to the QLineEdit widget
        self.index = index
        
    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)
