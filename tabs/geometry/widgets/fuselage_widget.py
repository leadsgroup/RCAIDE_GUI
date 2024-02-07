import os

from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QGridLayout

class FuselageWidget(QWidget):
    def __init__(self, index, on_delete):
        super(FuselageWidget, self).__init__()

        self.additional_data_values = {}
        self.index = index
        self.on_delete = on_delete

        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        # List of data labels
        data_labels = [
            "Percent X Location",
            "Percent Z Location",
            "Height",
            "Width"
        ]

        # Create QLineEdit frames with QDoubleValidator for numerical input
        for idx, label in enumerate(data_labels):
            row, col = divmod(idx, 2)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())

            # Set the width of the line edit
            line_edit.setFixedWidth(100)  # Adjust the width as needed

            self.grid_layout.addWidget(QLabel(label + ":"), row + 1, col * 3)
            self.grid_layout.addWidget(line_edit, row + 1, col * 3 + 1, 1, 2)

            # Store a reference to the QLineEdit in the dictionary
            self.additional_data_values[label] = line_edit

        # Add an append button
        row, col = (1, 2)
        self.append_button = QPushButton("Append Fuselage", self)
        self.append_button.clicked.connect(self.append_button_pressed)
        self.grid_layout.addWidget(self.append_button, row + 1, col * 3, 1, 2)

        # Add a delete button
        row, col = divmod(len(data_labels) + 1, 3)
        self.delete_button = QPushButton("Delete Fuselage", self)
        self.delete_button.clicked.connect(self.delete_button_pressed)
        self.grid_layout.addWidget(self.delete_button, row, col * 3, 1, 2)




    def append_button_pressed(self):
        """Append the entered data for the specified fuselage section."""
        # Retrieve the entered data from the QLineEdit widgets
        percent_x_location = float(self.additional_data_values["Percent X Location"].text())
        percent_z_location = float(self.additional_data_values["Percent Z Location"].text())
        height = float(self.additional_data_values["Height"].text())
        width = float(self.additional_data_values["Width"].text())
    
        print(f"Append Data for Fuselage Segment {self.index}: Percent X Location: {percent_x_location}, Percent Z Location: {percent_z_location}, Height: {height}, Width: {width}")
    
        # Increase the number of segments
        self.num_segments += 1
        # Update subtitles
        self.update_subtitles()
    
    def delete_button_pressed(self):
        print(f"Delete button pressed for Fuselage Segment {self.index}")
    
        if self.on_delete is None:
            print("on_delete is None")
            return
    
        self.on_delete(self.index)
        # Decrease the number of segments
        self.num_segments -= 1
        # Update subtitles after deletion
        self.update_subtitles()
