from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QScrollArea

from tabs.geometry.frames.geometry_frame import GeometryFrame, create_line_bar
from tabs.geometry.widgets.fuselage_section_widget import FuselageSectionWidget
from tabs.geometry.widgets.nacelle_section_widget import NacelleSectionWidget
from utilities import show_popup, Units
from widgets.data_entry_widget import DataEntryWidget


class FuselageFrame(QWidget, GeometryFrame):
    def __init__(self):
        """Create a frame for entering nacelle data."""
        super(FuselageFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        self.create_scroll_area()
        self.main_layout.addWidget(QLabel("<b>Fuselage</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.add_name_layout()

        # List of data labels
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

        # Add the data entry widget to the main layout
        self.data_entry_widget = DataEntryWidget(data_units_labels)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addWidget(create_line_bar())

        # Add the secctions layout to the main layout
        self.fuselage_sections_layout = QVBoxLayout()
        self.main_layout.addLayout(self.fuselage_sections_layout)

        self.add_buttons_layout()

        # Adds scroll function
        self.main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def create_scroll_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        self.main_layout = QVBoxLayout(scroll_content)
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout_scroll)

    def add_name_layout(self):
        name_layout = QHBoxLayout()
        spacer_left = QSpacerItem(50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_line_edit = QLineEdit(self)
        name_layout.addItem(spacer_left)
        name_layout.addWidget(QLabel("Name: "))
        name_layout.addWidget(self.name_line_edit)
        name_layout.addItem(spacer_right)
        self.main_layout.addLayout(name_layout)

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self):
        """Add the save, delete, and new buttons to the layout."""
        new_section_button = QPushButton("New Fuselage Section", self)
        save_button = QPushButton("Save Data", self)
        delete_button = QPushButton("Delete Data", self)
        new_button = QPushButton("New Fuselage Structure", self)

        new_section_button.clicked.connect(self.add_fuselage_section)
        save_button.clicked.connect(self.save_data)
        delete_button.clicked.connect(self.delete_data)
        new_button.clicked.connect(self.create_new_structure)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(new_section_button)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(new_button)
        self.main_layout.addLayout(buttons_layout)

    # noinspection DuplicatedCode
    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data = self.get_data_values()
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(self.tab_index, self.index, entered_data)
                return
            else:
                self.index = self.save_function(self.tab_index, data=entered_data, new=True)

            show_popup("Data Saved!", self)

    def add_fuselage_section(self):
        self.fuselage_sections_layout.addWidget(FuselageSectionWidget(
            self.fuselage_sections_layout.count(), self.delete_fuselage_section))

    def delete_fuselage_section(self, index):
        self.fuselage_sections_layout.itemAt(index).widget().deleteLater()
        self.fuselage_sections_layout.removeWidget(self.fuselage_sections_layout.itemAt(index).widget())
        self.fuselage_sections_layout.update()

        for i in range(index, self.fuselage_sections_layout.count()):
            item = self.fuselage_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, FuselageSectionWidget):
                widget.index = i

    # TODO: Implement proper deletion of data
    def delete_data(self):
        pass

    def create_new_structure(self):
        """Create a new nacelle structure."""
        # Clear the main data values
        self.data_entry_widget.clear_values()
        self.name_line_edit.clear()

        # Clear the nacelle sections
        for i in range(self.fuselage_sections_layout.count()):
            self.fuselage_sections_layout.itemAt(i).widget().deleteLater()
        self.fuselage_sections_layout.update()
        self.index = -1

    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        data = self.data_entry_widget.get_values()

        data["sections"] = []
        for i in range(self.fuselage_sections_layout.count()):
            item = self.fuselage_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, FuselageSectionWidget):
                data["sections"].append(widget.get_data_values())

        data["name"] = self.name_line_edit.text()
        return data

    def load_data(self, data, index):
        """Load the data into the widgets.

        Args:
            data: The data to be loaded into the widgets.
            index: The index of the data in the list.
        """
        self.data_entry_widget.load_data(data)

        for section in data["sections"]:
            self.fuselage_sections_layout.addWidget(FuselageSectionWidget(
                self.fuselage_sections_layout.count(), self.delete_fuselage_section, section))

        self.name_line_edit.setText(data["name"])
        self.index = index
