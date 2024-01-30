import os

from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QGridLayout, QLineEdit, QHBoxLayout, \
    QFileDialog

from utilities import show_popup


class NacelleFrame(QWidget):
    def __init__(self):
        super(NacelleFrame, self).__init__()
        self.coordinate_filename = ""
        self.data_values = {}

        layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()

        header_layout.addWidget(QLabel("Add Nacelle"))

        # Add buttons for appending and deleting data
        append_button = QPushButton("Append Data", self)
        delete_button = QPushButton("Delete Data", self)

        append_button.clicked.connect(self.append_data)
        delete_button.clicked.connect(self.delete_data)

        header_layout.addWidget(append_button)
        header_layout.addWidget(delete_button)

        layout.addLayout(header_layout)
        # layout.addWidget(Color("lightblue"))

        # Create a grid layout with 3 columns
        grid_layout = QGridLayout()

        # List of data labels
        data_labels = [
            "Length",
            "Inlet Diameter",
            "Diameter",
            "Wetted Area",
            "Origin",
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
        grid_layout.addWidget(get_file_button, row, col * 3 + 1, 1, 2)
        # Add the grid layout to the home layout
        layout.addLayout(grid_layout)

        self.setLayout(layout)

    def get_file_name(self):
        file_filter = "Data File (*.csv)"
        self.coordinate_filename = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.getcwd(),
            filter=file_filter
        )[0]

        print(self.coordinate_filename)

    def append_data(self):
        """Append the entered data to a list or perform any other action."""
        entered_data = self.get_data_values()
        # Implement appending logic here, e.g., append to a list
        print("Appending Data:", entered_data)
        show_popup("Data Saved!", self)

    def delete_data(self):
        """Delete the entered data or perform any other action."""
        entered_data = self.get_data_values()
        # Implement deletion logic here, e.g., clear the entries
        print("Deleting Data:", entered_data)
        for line_edit in self.data_values.values():
            line_edit.clear()
        show_popup("Data Erased!", self)

    # noinspection PyTypeChecker
    def get_data_values(self):
        """Retrieve the entered data values from the dictionary."""
        temp = {label: float(line_edit.text()) if line_edit.text() else 0.0
                for label, line_edit in self.data_values.items()}
        temp["Coordinate Filename"] = self.coordinate_filename
        return temp
