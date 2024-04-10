from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, \
    QSizePolicy, QSpacerItem, QLineEdit

from tabs.geometry.frames.geometry_frame import GeometryFrame
from tabs.geometry.widgets.fuselage_section_widget import FuselageSectionWidget
from utilities import show_popup, Units
from widgets.data_entry_widget import DataEntryWidget


# ================================================================================================================================================

# Main Fuselage Frame

# ================================================================================================================================================

class FuselageFrame(QWidget, GeometryFrame):
    def __init__(self):
        super(FuselageFrame, self).__init__()

        self.index = -1
        self.tab_index = -1
        self.save_function = None

        data_units_labels = [
            ("Fineness Nose", Units.Unitless),
            ("Fineness Tail", Units.Unitless),
            ("Lengths Nose", Units.Length),
            ("Lengths Tail", Units.Length),
            ("Lengths Cabin", Units.Length),
            ("Lengths Total", Units.Length),
            ("Lengths Forespace", Units.Length),
            ("Lengths Aftspace", Units.Length),
            ("Width", Units.Length),
            ("Heights Maximum", Units.Length),
            ("Height at Quarter", Units.Length),
            ("Height at Three Quarters", Units.Length),
            ("Height at Wing Root Quarter Chord", Units.Length),
            ("Areas Side Projected", Units.Area),
            ("Area Wetted", Units.Area),
            ("Area Front Projected", Units.Area),
            ("Effective Diameter", Units.Length),
        ]

        # List to store data values fuselage sections
        self.fuselage_sections_layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        label = QLabel("<u><b>Main Fuselage Frame</b></u>")

        layout = self.create_scroll_layout()

        header_layout.addWidget(label)
        layout.addLayout(header_layout)

        name_layout = QHBoxLayout()
        spacer_left = QSpacerItem(50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_line_edit = QLineEdit()
        name_layout.addItem(spacer_left)
        name_layout.addWidget(QLabel("Name:"))
        name_layout.addWidget(self.name_line_edit)
        name_layout.addItem(spacer_right)

        layout.addLayout(name_layout)

        # Add the grid layout for the main fuselage section to the main layout
        self.data_entry_widget: DataEntryWidget = DataEntryWidget(data_units_labels)
        layout.addWidget(self.data_entry_widget)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Add the layout for additional fuselage sections to the main layout
        layout.addLayout(self.fuselage_sections_layout)

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add Fuselage Section Button
        add_section_button = QPushButton("Add Fuselage Section", self)
        add_section_button.clicked.connect(self.add_fuselage_section)
        button_layout.addWidget(add_section_button)

        # Append All Fuselage Section Data Button
        append_all_data_button = QPushButton("Save Fuselage Data", self)
        append_all_data_button.clicked.connect(self.save_data)
        button_layout.addWidget(append_all_data_button)

        # Delete Nacelle Data Button
        delete_data_button = QPushButton("Delete Fuselage Data", self)
        delete_data_button.clicked.connect(self.delete_data)
        button_layout.addWidget(delete_data_button)

        # Create new nacelle structure button
        new_fuselage_structure_button = QPushButton("New Fuselage Structure", self)
        new_fuselage_structure_button.clicked.connect(self.create_new_structure)
        button_layout.addWidget(new_fuselage_structure_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def get_data_values(self):
        """Retrieve the entered data values from the dictionary for the main fuselage section."""
        data = self.data_entry_widget.get_values()
        data["name"] = self.name_line_edit.text()

        # Collect data from additional fuselage_widget
        additional_data = []
        for index in range(self.fuselage_sections_layout.count()):
            widget = self.fuselage_sections_layout.itemAt(index).widget()
            additional_data.append(widget.get_data_values())

        data["sections"] = additional_data
        return data

    def save_data(self):
        """Append the entered data to a list or perform any other action."""
        entered_data = self.get_data_values()

        print("Main Fuselage Data:", entered_data)

        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(self.tab_index, self.index, entered_data)
                return
            else:
                self.index = self.save_function(self.tab_index, data=entered_data, new=True)

            show_popup("Data Saved!", self)

    def load_data(self, data, index):
        self.data_entry_widget.load_data(data)
        self.name_line_edit.setText(data["name"])

        # Make sure sections don't already exist
        while self.fuselage_sections_layout.count():
            item = self.fuselage_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for section_data in data["sections"]:
            self.fuselage_sections_layout.addWidget(FuselageSectionWidget(
                self.fuselage_sections_layout.count(), self.on_delete_button_pressed, section_data))

    def delete_data(self):
        """Delete the entered data or perform any other action."""
        self.data_entry_widget.clear_values()

    def add_fuselage_section(self):
        self.fuselage_sections_layout.addWidget(
            FuselageSectionWidget(self.fuselage_sections_layout.count(), self.on_delete_button_pressed))

    def on_delete_button_pressed(self, index):
        self.fuselage_sections_layout.itemAt(index).widget().deleteLater()
        self.fuselage_sections_layout.removeWidget(self.fuselage_sections_layout.itemAt(index).widget())
        self.fuselage_sections_layout.update()
        print("Deleted Fuselage at Index:", index)

        for i in range(index, self.fuselage_sections_layout.count()):
            self.fuselage_sections_layout.itemAt(i).widget().index = i
            print("Updated Index:", i)

    def update_units(self, line_edit, unit_combobox):
        pass

    def set_save_function(self, function):
        self.save_function = function

    def set_tab_index(self, index):
        self.tab_index = index

    def create_new_structure(self):
        """Create a new fuselage structure."""

        # Clear the main data values
        self.data_entry_widget.clear_values()

        # Clear the name line edit
        while self.fuselage_sections_layout.count():
            item = self.fuselage_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.name_line_edit.clear()
        self.index = -1

    def create_scroll_layout(self):
        # Create a scroll area

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # Allow the widget inside to resize with the scroll area

        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)

        return layout
