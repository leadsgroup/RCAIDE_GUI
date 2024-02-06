from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QGridLayout, QLineEdit, QHBoxLayout, QScrollArea, \
    QSpacerItem, QSizePolicy

from utilities import show_popup


class LandingGearFrame(QWidget):
    def __init__(self):
        super(LandingGearFrame, self).__init__()

        self.main_data_values = {}

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()

        layout = QVBoxLayout(scroll_content)

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Landing Gear</b>"))

        # Add buttons for appending and deleting data
        save_button = QPushButton("Save Data", self)
        delete_button = QPushButton("Delete Data", self)

        save_button.clicked.connect(self.append_data)
        delete_button.clicked.connect(self.delete_data)

        header_layout.addWidget(save_button)
        header_layout.addWidget(delete_button)

        layout.addLayout(header_layout)
        # layout.addWidget(Color("lightblue"))

        # Create a grid layout with 3 columns
        grid_layout = QGridLayout()

        # List of data labels
        data_labels = [
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
            self.main_data_values[label] = line_edit

        # Add the grid layout to the home layout
        layout.addLayout(grid_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)

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
        for line_edit in self.main_data_values.values():
            line_edit.clear()
        show_popup("Data Erased!", self)

    def get_data_values(self):
        """Retrieve the entered data values from the dictionary."""
        return {label: float(line_edit.text()) if line_edit.text() else 0.0
                for label, line_edit in self.main_data_values.items()}
