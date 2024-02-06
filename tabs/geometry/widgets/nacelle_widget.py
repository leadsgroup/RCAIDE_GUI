import os

from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QFileDialog, QPushButton, QLabel, QLineEdit, QGridLayout


class NacelleWidget(QWidget):
    def __init__(self, index, on_delete):
        super(NacelleWidget, self).__init__()

        self.data_values = {}
        self.coordinate_filename = ""
        self.index = index
        self.on_delete = on_delete

        grid_layout = QGridLayout()
        # TODO: Add nacelle name

        # List of data labels
        data_labels = [
            "Length",
            "Inlet Diameter",
            "Diameter",
            "Origin X",
            "Origin Y",
            "Origin Z",
            "Wetted Area",
            "Flow Through",
            "Airfoil Flag",
        ]

        # Create QLineEdit frames with QDoubleValidator for numerical input
        for index, label in enumerate(data_labels):
            row, col = divmod(index, 3)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())

            # Set the width of the line edit
            line_edit.setFixedWidth(100)  # Adjust the width as needed

            grid_layout.addWidget(QLabel(label + ":"), row, col * 3)
            grid_layout.addWidget(line_edit, row, col * 3 + 1, 1, 2)

            # Store a reference to the QLineEdit in the dictionary
            self.data_values[label] = line_edit

        row, col = divmod(len(data_labels), 3)
        grid_layout.addWidget(QLabel("Coordinate File:"), row, col * 3)
        get_file_button = QPushButton("...", self)
        get_file_button.clicked.connect(self.get_file_name)
        get_file_button.setFixedWidth(100)
        grid_layout.addWidget(get_file_button, row, col * 3 + 1, 1, 2)

        # Add a delete button
        row, col = divmod(len(data_labels) + 1, 3)
        delete_button = QPushButton("Delete Nacelle", self)
        delete_button.clicked.connect(self.delete_button_pressed)
        grid_layout.addWidget(delete_button, row, col * 3, 1, 2)

        self.setLayout(grid_layout)

    def get_file_name(self):
        file_filter = "Data File (*.csv)"
        self.coordinate_filename = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.getcwd(),
            filter=file_filter
        )[0]

        print(self.coordinate_filename)

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)
