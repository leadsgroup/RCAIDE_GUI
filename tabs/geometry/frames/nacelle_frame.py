import os

from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy, QLineEdit, QGridLayout, QFileDialog

from tabs.geometry.frames.geometry_frame import GeometryFrame
from tabs.geometry.widgets.nacelle_section_widget import NacelleSectionWidget
from utilities import show_popup, Units
from widgets.unit_picker_widget import UnitPickerWidget


class NacelleFrame(QWidget, GeometryFrame):
    def __init__(self):
        """Constructor for the NacelleFrame class."""
        super(NacelleFrame, self).__init__()
        self.data_fields = {}
        self.nacelle_sections_layout = QVBoxLayout()
        self.coordinate_filename = ""
        self.save_function = None
        self.tab_index = -1
        self.index = -1
        self.name_line_edit: QLineEdit | None = None

        # Create a scroll area
        scroll_area = QScrollArea()
        # Allow the widget inside to resize with the scroll area
        scroll_area.setWidgetResizable(True)

        # Create a widget to contain the layout
        scroll_content = QWidget()
        # Set the main layout inside the scroll content
        layout = QVBoxLayout(scroll_content)

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Nacelle</b>"))

        layout.addLayout(header_layout)
        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        self.main_nacelle_widget = self.make_nacelle_widget()
        # Add the grid layout to the home layout
        layout.addWidget(self.main_nacelle_widget)

        layout.addWidget(line_bar)
        layout.addLayout(self.nacelle_sections_layout)

        # Add the layout for additional fuselage sections to the main layout

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add Nacelle Button
        add_section_button = QPushButton("Add Nacelle Section", self)
        add_section_button.clicked.connect(self.add_nacelle_section)
        button_layout.addWidget(add_section_button)

        # Save Nacelle Data Button
        save_data_button = QPushButton("Save Nacelle Data", self)
        save_data_button.clicked.connect(self.save_data)
        button_layout.addWidget(save_data_button)

        # Delete Nacelle Data Button
        delete_data_button = QPushButton("Delete Nacelle Data", self)
        delete_data_button.clicked.connect(self.delete_data)
        button_layout.addWidget(delete_data_button)

        # Create new nacelle structure button
        new_nacelle_structure_button = QPushButton("New Nacelle Structure", self)
        new_nacelle_structure_button.clicked.connect(self.create_new_structure)
        button_layout.addWidget(new_nacelle_structure_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)

    def get_file_name(self):
        """Open a file dialog to select a file and store the file name.

        The file name is stored in the self.coordinate_filename attribute.
        """
        file_filter = "Data File (*.csv)"
        self.coordinate_filename = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.getcwd(),
            filter=file_filter
        )[0]

        print(self.coordinate_filename)

    def make_nacelle_widget(self):
        """Create a widget for the nacelle section.

        Returns:
            QWidget: The main nacelle widget."""
        main_nacelle_widget = QWidget()
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()

        name_layout = QHBoxLayout()
        # add spacing
        spacer_left = QSpacerItem(50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        name_layout.addItem(spacer_left)
        name_layout.addWidget(QLabel("Name: "))
        self.name_line_edit = QLineEdit(self)
        name_layout.addWidget(self.name_line_edit)
        name_layout.addItem(spacer_right)
        main_layout.addLayout(name_layout)

        # List of data labels
        data_units_labels = [
            ("Length", Units.Length),
            ("Inlet Diameter", Units.Length),
            ("Diameter", Units.Length),
            ("Origin X", Units.Length),
            ("Origin Y", Units.Length),
            ("Origin Z", Units.Length),
            ("Wetted Area", Units.Area),
            ("Flow Through", Units.Unitless),
            ("Airfoil Flag", Units.Unitless),
        ]

        # Create QLineEdit frames with QDoubleValidator for numerical input
        # Create a grid layout with 3 columns
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

        row, col = divmod(len(data_units_labels), 2)
        grid_layout.addWidget(QLabel("Coordinate File:"), row, col * 3)
        get_file_button = QPushButton("...", self)
        get_file_button.clicked.connect(self.get_file_name)
        get_file_button.setFixedWidth(100)
        grid_layout.addWidget(get_file_button, row, col * 3 + 1, 1, 2)

        main_layout.addLayout(grid_layout)

        main_nacelle_widget.setLayout(main_layout)
        return main_nacelle_widget

    def add_nacelle_section(self):
        self.nacelle_sections_layout.addWidget(NacelleSectionWidget(
            self.nacelle_sections_layout.count(), self.on_delete_button_pressed))

    def set_save_function(self, function):
        self.save_function = function

    def set_tab_index(self, index):
        self.tab_index = index

    def on_delete_button_pressed(self, index):
        self.nacelle_sections_layout.itemAt(index).widget().deleteLater()
        self.nacelle_sections_layout.removeWidget(self.nacelle_sections_layout.itemAt(index).widget())
        self.nacelle_sections_layout.update()
        print("Deleted Nacelle at Index:", index)

        for i in range(index, self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, NacelleSectionWidget):
                widget.index = i
                print("Updated Index:", i)

    # # noinspection PyTypeChecker
    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        data = {}
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value = float(line_edit.text()) if line_edit.text() else 0.0
            data[label] = unit_picker.apply_unit(value), unit_picker.current_index

        # Get the values from the text fields
        data["Coordinate File"] = self.coordinate_filename
        data["name"] = self.name_line_edit.text()
        data["sections"] = []

        # Loop through the sections and get the data from each widget
        for i in range(self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()

            # Each of the widgets has its own get_data_values method that is called to fetch their data
            if widget is not None and isinstance(widget, NacelleSectionWidget):
                data["sections"].append(widget.get_data_values())

        return data

    # noinspection DuplicatedCode
    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data = self.get_data_values()
        print("Saving Data:", entered_data)
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(self.tab_index, self.index, entered_data)
                return
            else:
                self.index = self.save_function(self.tab_index, data=entered_data, new=True)

            show_popup("Data Saved!", self)

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


        self.coordinate_filename = data["Coordinate File"]

        # Make sure sections don't already exist
        while self.nacelle_sections_layout.count():
            item = self.nacelle_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Add all the sections
        for section_data in data["sections"]:
            self.nacelle_sections_layout.addWidget(NacelleSectionWidget(
                self.nacelle_sections_layout.count(), self.on_delete_button_pressed, section_data))

        self.index = index

    def create_new_structure(self):
        """Create a new nacelle structure."""

        # Clear the main data values
        for data_field in self.data_fields.values():
            line_edit, unit_picker = data_field
            line_edit.clear()
            unit_picker.set_index(0)

        # Clear the name line edit
        while self.nacelle_sections_layout.count():
            item = self.nacelle_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.name_line_edit.clear()
        self.index = -1

    def delete_data(self):
        pass
