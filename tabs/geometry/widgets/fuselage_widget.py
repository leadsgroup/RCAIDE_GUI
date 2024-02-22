import os

from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QFileDialog, QPushButton, QLabel, QLineEdit, QGridLayout


class FuselageWidget(QWidget):
    def __init__(self, index, on_delete):
        super(FuselageWidget, self).__init__()

        self.data_values = {}
        self.index = index
        self.on_delete = on_delete

        grid_layout = QGridLayout()
 
 
        self.section_name_edit = QLineEdit(self)
        grid_layout.addWidget(QLabel("<u><b>Fuselage Section: </b></u>"), 0, 0)
        grid_layout.addWidget(self.section_name_edit, 0, 1, 1, 2)

        # List of data labels
        data_labels = [
            "Percent X Location",
            "Percent Z Location",
            "Height",
            "Width",
        ]

        # Create QLineEdit frames with QDoubleValidator for numerical input
        for index, label in enumerate(data_labels):
            row, col = divmod(index , 2)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())

            # Set the width of the line edit
            line_edit.setFixedWidth(100)  # Adjust the width as needed

            grid_layout.addWidget(QLabel(label + ":"), row+1, col * 3)
            grid_layout.addWidget(line_edit, row+1, col * 3 + 1, 1, 2)

            # Store a reference to the QLineEdit in the dictionary
            self.data_values[label] = line_edit



        # Add a delete button
        row, col = divmod(len(data_labels) + 2, 1)
        delete_button = QPushButton("Delete Fuselage Segment", self)
        delete_button.clicked.connect(self.delete_button_pressed)
        grid_layout.addWidget(delete_button, row, col * 3, 1, 5)

        self.setLayout(grid_layout)


    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)
        
    def get_data_values(self):
        title = self.section_name_edit.text()
        data_values = {label: float(line_edit.text()) if line_edit.text() else 0.0
                       for label, line_edit in self.data_values.items()}
        return title, data_values