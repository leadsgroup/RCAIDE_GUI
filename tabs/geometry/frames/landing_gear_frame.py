from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QGridLayout, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QScrollArea, QFrame

from tabs.geometry.frames.geometry_frame import GeometryFrame
from utilities import show_popup, Units
from widgets.unit_picker_widget import UnitPickerWidget


class LandingGearFrame(QWidget, GeometryFrame):
    def __init__(self):
        """Create a frame for entering landing gear data."""
        super(LandingGearFrame, self).__init__()

        # TODO: Add landing gear types in the future

        self.data_fields = {}
        self.tab_index = -1
        self.index = -1
        self.save_function = None

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()

        layout = QVBoxLayout(scroll_content)

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Landing Gear</b>"))

        layout.addLayout(header_layout)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        name_layout = QHBoxLayout()
        # add spacing
        spacer_left = QSpacerItem(50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        name_layout.addItem(spacer_left)
        name_layout.addWidget(QLabel("Name: "))
        self.name_line_edit = QLineEdit(self)
        name_layout.addWidget(self.name_line_edit)
        name_layout.addItem(spacer_right)
        layout.addLayout(name_layout)
        # layout.addWidget(Color("lightblue"))

        # TODO: Split into different functions

        # Create a grid layout with 3 columns
        grid_layout = QGridLayout()

        # List of data labels
        data_units_labels = [
            ("Main Tire Diameter", Units.Length),
            ("Nose Tire Diameter", Units.Length),
            ("Main Strut Length", Units.Length),
            ("Nose Strut Length", Units.Length),
            ("Main Units", Units.Count),
            ("Nose Units", Units.Count),
            ("Main Wheels", Units.Count),
            ("Nose Wheels", Units.Count)
        ]

        # Create QLineEdit frames with QDoubleValidator for numerical input
        for index, label in enumerate(data_units_labels):
            row, col = divmod(index, 2)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())
            # Set the width of the line edit
            line_edit.setFixedWidth(100)  # Adjust the width as needed

            unit_picker = UnitPickerWidget(label[1])

            grid_layout.addWidget(QLabel(label[0] + ":"), row, col * 3)
            grid_layout.addWidget(line_edit, row, col * 3 + 1, 1, 2)
            grid_layout.addWidget(unit_picker, row, col * 3 + 2, 1, 1)

            # Store a reference to the QLineEdit in the dictionary
            self.data_fields[label[0]] = (line_edit, unit_picker)

        # Add the grid layout to the home layout
        layout.addLayout(grid_layout)

        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")
        layout.addWidget(line_above_buttons)

        # Add buttons for appending and deleting data
        save_button = QPushButton("Save Data", self)
        delete_button = QPushButton("Delete Data", self)
        new_button = QPushButton("New Landing Gear Structure", self)

        save_button.clicked.connect(self.save_data)
        delete_button.clicked.connect(self.delete_data)
        new_button.clicked.connect(self.create_new_structure)

        buttons_layout = QHBoxLayout(scroll_content)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(new_button)
        layout.addLayout(buttons_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)

    # noinspection DuplicatedCode
    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data = self.get_data_values()
        # Implement appending logic here, e.g., append to a list
        print("Saving Data:", entered_data)
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(self.tab_index, self.index, entered_data)
                return
            else:
                self.index = self.save_function(self.tab_index, data=entered_data, new=True)

            show_popup("Data Saved!", self)

    # TODO: Implement proper deletion of data
    def delete_data(self):
        pass

    def create_new_structure(self):
        """Create a new landing gear structure."""
        # Clear the main data values
        for data_field in self.data_fields.values():
            line_edit, unit_picker = data_field
            line_edit.clear()
            unit_picker.set_index(0)
        self.name_line_edit.clear()
        self.index = -1

    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        data = {}
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value = float(line_edit.text()) if line_edit.text() else 0.0
            data[label] = value, unit_picker.current_index

        data["name"] = self.name_line_edit.text()
        return data

    def load_data(self, data, index):
        """Load the data into the widgets.

        Args:
            data: The data to be loaded into the widgets.
            index: The index of the data in the list.
        """
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value, index = data[label]
            line_edit.setText(str(value))
            unit_picker.set_index(index)

        self.name_line_edit.setText(data["name"])
        self.index = index

    def set_save_function(self, function):
        """Set the save function to be called when the save button is pressed.

        Args:
            function: The function to be called.
        """
        self.save_function = function

    def set_tab_index(self, index):
        """Set the tab index for the frame.

        Args:
            index: The index of the tab."""
        self.tab_index = index
