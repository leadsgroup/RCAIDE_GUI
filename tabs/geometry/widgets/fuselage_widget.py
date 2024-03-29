import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget)
from utilities import Units
from widgets.unit_picker_widget import UnitPickerWidget

class FuselageWidget(QWidget):
    def __init__(self, index, on_delete, section_data = None):
        super(FuselageWidget, self).__init__()

        self.data_fields = {}
        self.index = index
        self.on_delete = on_delete

        self.name_layout = QHBoxLayout()
        self.init_ui(section_data)
 
    def init_ui(self, section_data):
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()
        # add spacing
        spacer_left = QSpacerItem(80, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(300, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_layout.addItem(spacer_left)
        self.name_layout.addWidget(QLabel("Segment Name: "))
        self.name_layout.addWidget(QLineEdit(self))
        self.name_layout.addItem(spacer_right)

        main_layout.addLayout(self.name_layout) 
 

        # List of data labels
        data_units_labels = [
            ("Percent X Location", Units.Unitless),
            ("Percent Z Location",Units.Unitless),
            ("Height", Units.Length),
            ("Width", Units.Length)
        ]

        # Create QLineEdit frames with QDoubleValidator for numerical input
        for index, label in enumerate(data_units_labels):
            row, col = divmod(index , 2)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())

            # Set the width of the line edit
            line_edit.setFixedWidth(100)  # Adjust the width as needed
            
            unit_picker = UnitPickerWidget(label[1])
            
            grid_layout.addWidget(QLabel(label[0] + ":"), row, col * 3)
            grid_layout.addWidget(line_edit, row, col * 3 + 1, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
            grid_layout.addWidget(unit_picker, row, col * 3 + 2, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
            
            # Store a reference to the QLineEdit in the dictionary
            self.data_fields[label[0]] = (line_edit, unit_picker)


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
        data = {}
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value = float(line_edit.text()) if line_edit.text() else 0.0
            data[label] = unit_picker.apply_unit(value), unit_picker.current_index

        data["segment name"] = self.name_layout.itemAt(2).widget().text()
        return data
    
    

    def load_data_values(self, section_data):
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value, index = section_data[label]
            line_edit.setText(str(value))
            unit_picker.set_index(index)

        self.name_layout.itemAt(2).widget().setText(section_data["segment name"])

    
    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)
        
