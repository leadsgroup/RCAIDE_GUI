from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox

from widgets.color import Color


class FuselageFrame(QWidget):
    def __init__(self):
        super(FuselageFrame, self).__init__()

        # Dictionary to store the entered values
        self.data_values = {}

        layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()

        header_layout.addWidget(QLabel("Add Fuselage Component"))

        # Add buttons for appending and deleting data
        append_button = QPushButton("Append Data", self)
        delete_button = QPushButton("Delete Data", self)

        append_button.clicked.connect(self.append_data)
        delete_button.clicked.connect(self.delete_data)

        header_layout.addWidget(append_button)
        header_layout.addWidget(delete_button)

        layout.addLayout(header_layout)
        layout.addWidget(Color("lightblue"))

        # Create a grid layout with 3 columns
        grid_layout = QGridLayout()

        # List of data labels
        data_labels = ["Fineness Nose", "Fineness Tail", "Lengths Nose", "Lengths Tail", "Lengths Cabin",
                       "Lengths Total", "Lengths Forespace", "Lengths Aftspace", "Width", "Heights Maximum",
                       "Height at Quarter", "Height at Three Quarters", "Height at Wing Root Quarter Chord",
                       "Areas Side Projected", "Area Wetted", "Area Front Projected", "Effective Diameter"]

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
        self.show_popup("Data Saved!", self)

    def delete_data(self):
        """Delete the entered data or perform any other action."""
        entered_data = self.get_data_values()
        # Implement deletion logic here, e.g., clear the entries
        print("Deleting Data:", entered_data)
        for line_edit in self.data_values.values():
            line_edit.clear()
        self.show_popup("Data Erased!", self)

    def get_data_values(self):
        """Retrieve the entered data values from the dictionary."""
        return {label: float(line_edit.text()) if line_edit.text() else 0.0
                for label, line_edit in self.data_values.items()}

    def show_popup(self, message, parent):
        """Display a pop-up message for 2 seconds."""
        popup = QMessageBox(parent)
        popup.setWindowTitle("Info")
        popup.setText(message)
        # This line seemed to make it impossible to close the popup
        # popup.setStandardButtons(QMessageBox.StandardButton.NoButton)
        popup.setStyleSheet("QLabel{min-width: 300px;}")
        popup.show()
        #
        # # Use QTimer to close the popup after 2 seconds
        timer = QTimer(popup)
        timer.setSingleShot(True)
        timer.timeout.connect(popup.close)
        timer.start(2000)  # 2000 milliseconds (2 seconds)
