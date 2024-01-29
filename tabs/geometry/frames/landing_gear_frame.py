from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QGridLayout, QLineEdit, QHBoxLayout

from utilities import show_popup


class LandingGearFrame(QWidget):
    def __init__(self):
        super(LandingGearFrame, self).__init__()
        self.data_values = {}

        layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()

        header_layout.addWidget(QLabel("Add Landing Gear"))

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
        data_labels = landing_gear_names = [
            "Main Tire Diameter",
            "Nose Tire Diameter",
            "Main Strut Length",
            "Nose Strut Length",
            "Main Units",
            "Nose Units",
            "Main Wheels",
            "Nose Wheels"
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

        # Add the grid layout to the home layout
        layout.addLayout(grid_layout)

        self.setLayout(layout)

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

    def get_data_values(self):
        """Retrieve the entered data values from the dictionary."""
        return {label: float(line_edit.text()) if line_edit.text() else 0.0
                for label, line_edit in self.data_values.items()}
