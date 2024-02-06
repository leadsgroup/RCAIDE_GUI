import os

from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QGridLayout, QLineEdit, QHBoxLayout, QScrollArea, QFrame, QSpacerItem, QSizePolicy, QFileDialog



from utilities import show_popup


class NacelleFrame(QWidget):
    def __init__(self):
        super(NacelleFrame, self).__init__()
        self.coordinate_filenames = {}
        self.main_data_values = {}

         # List to store data values for additional fuselage sections
        self.additional_data_values = {}

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget inside to resize with the scroll area

        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Nacelles</b>"))

        # Add buttons for appending and deleting data
        # append_button = QPushButton("Append Data", self)
        # delete_button = QPushButton("Delete Data", self)

        # append_button.clicked.connect(self.append_data)
        # delete_button.clicked.connect(self.delete_data)

        # header_layout.addWidget(append_button)
        # header_layout.addWidget(delete_button)

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
            self.main_data_values[label] = line_edit

        row, col = divmod(len(data_labels), 3)
        grid_layout.addWidget(QLabel("Coordinate File:"), row, col * 3)
        get_file_button = QPushButton("...", self)
        get_file_button.clicked.connect(self.get_file_name)
        grid_layout.addWidget(get_file_button, row, col * 3 + 1, 1, 2)

        
        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: white;")
        
        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Add the grid layout to the home layout
        layout.addLayout(grid_layout)
        
        
        # Initialize additional layout for fuselage sections
        self.additional_layout = QVBoxLayout()
        
        # Add the layout for additional fuselage sections to the main layout
        layout.addLayout(self.additional_layout)
        
        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: white;")
        
        layout.addWidget(line_above_buttons)
       
        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()
        
        # Add Nacelle Button
        add_section_button = QPushButton("Add Nacelle", self)
        # add_section_button.clicked.connect(self.add_nacelle)
        button_layout.addWidget(add_section_button)
        
        # Append All Fuselage Section Data Button
        append_all_data_button = QPushButton("Append All Nacelle Data", self)
        # append_all_data_button.clicked.connect(self.append_all_data)
        button_layout.addWidget(append_all_data_button)
        
        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)

    def get_file_name(self):
        file_filter = "Data File (*.csv)"
        self.coordinate_filenames = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.getcwd(),
            filter=file_filter
        )[0]

        print(self.coordinate_filenames)

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

    # noinspection PyTypeChecker
    def get_data_values(self):
        """Retrieve the entered data values from the dictionary."""
        temp = {label: float(line_edit.text()) if line_edit.text() else 0.0
                for label, line_edit in self.main_data_values.items()}
        temp["Coordinate Filename"] = self.coordinate_filenames
        return temp
