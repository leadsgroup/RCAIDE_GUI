import RCAIDE
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QScrollArea

from tabs.geometry.frames.geometry_frame import GeometryFrame
from tabs.geometry.widgets import NacelleSectionWidget
from utilities import show_popup, create_line_bar, Units
from widgets import DataEntryWidget


class NacelleFrame(QWidget, GeometryFrame):
    def __init__(self):
        """Create a frame for entering nacelle data."""
        super(NacelleFrame, self).__init__()

        self.create_scroll_area()
        self.main_layout.addWidget(QLabel("<b>Nacelle</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.add_name_layout()

        # List of data labels
        data_units_labels = [
            ("Length", Units.Length),
            ("Inlet Diameter", Units.Length),
            ("Diameter", Units.Length),
            ("Origin", Units.Position),
            ("Wetted Area", Units.Area),
            ("Flow Through", Units.Boolean),
            ("Airfoil Flag", Units.Boolean),
            ("Airfoil Coordinate File", Units.Unitless)
        ]

        # Add the data entry widget to the main layout
        self.data_entry_widget: DataEntryWidget = DataEntryWidget(
            data_units_labels)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addWidget(create_line_bar())

        # Add the secctions layout to the main layout
        self.nacelle_sections_layout = QVBoxLayout()
        self.main_layout.addLayout(self.nacelle_sections_layout)

        self.add_buttons_layout()

        # Adds scroll function
        self.main_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def create_scroll_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        self.main_layout: QVBoxLayout = QVBoxLayout(scroll_content)
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout_scroll)

    def add_name_layout(self):
        name_layout = QHBoxLayout()
        spacer_left = QSpacerItem(
            50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(
            200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_line_edit: QLineEdit = QLineEdit(self)
        name_layout.addItem(spacer_left)
        name_layout.addWidget(QLabel("Name: "))
        name_layout.addWidget(self.name_line_edit)
        name_layout.addItem(spacer_right)
        self.main_layout.addLayout(name_layout)

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self):
        """Add the save, delete, and new buttons to the layout."""
        new_section_button = QPushButton("New Nacelle Section", self)
        save_button = QPushButton("Save Data", self)
        delete_button = QPushButton("Delete Data", self)
        new_button = QPushButton("New Nacelle Structure", self)

        new_section_button.clicked.connect(self.add_nacelle_section)
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
        entered_data, v_comp = self.get_data_values()
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(
                    self.tab_index, self.index, entered_data)
                return
            else:
                self.index = self.save_function(
                    self.tab_index, vehicle_component=v_comp, data=entered_data, new=True)

            show_popup("Data Saved!", self)

    def add_nacelle_section(self):
        self.nacelle_sections_layout.addWidget(NacelleSectionWidget(
            self.nacelle_sections_layout.count(), self.delete_nacelle_section))

    def delete_nacelle_section(self, index):
        item = self.nacelle_sections_layout.itemAt(index)
        if item is None:
            return

        widget = item.widget()
        if widget is None or not isinstance(widget, NacelleSectionWidget):
            return

        widget.deleteLater()
        self.nacelle_sections_layout.removeWidget(widget)
        self.nacelle_sections_layout.update()

        for i in range(index, self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, NacelleSectionWidget):
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
        for i in range(self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, NacelleSectionWidget):
                widget.deleteLater()

        self.nacelle_sections_layout.update()
        self.index = -1

    def create_rcaide_structure(self, data):
        """Create a nacelle structure from the given data.

        Args:
            data: The data to create the nacelle structure from.
        """
        nacelle = RCAIDE.Library.Components.Nacelles.Nacelle()
        nacelle.diameter = data["Diameter"][0]
        nacelle.inlet_diameter = data["Inlet Diameter"][0]
        nacelle.length = data["Length"][0]
        nacelle.tags = data["name"]
        origin = data["Origin"][0]
        nacelle.origin = origin
        nacelle.areas.wetted = data["Wetted Area"][0]
        nacelle.flow_through = data["Flow Through"][0]
        nacelle.Airfoil.NACA_4_series_flag = data["Airfoil Flag"][0]
        nacelle.Airfoil.coordinate_file = data["Airfoil Coordinate File"][0]

        return nacelle

    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data_si["name"] = self.name_line_edit.text()

        nacelle = self.create_rcaide_structure(data_si)

        data["sections"] = []
        for i in range(self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, NacelleSectionWidget):
                segment_data, segment = widget.get_data_values()
                data["sections"].append(segment_data)
                nacelle.append_segment(segment)

        data["name"] = self.name_line_edit.text()
        return data, nacelle

    def load_data(self, data, index):
        """Load the data into the widgets.

        Args:
            data: The data to be loaded into the widgets.
            index: The index of the data in the list.
        """
        self.data_entry_widget.load_data(data)

        for section in data["sections"]:
            self.nacelle_sections_layout.addWidget(NacelleSectionWidget(
                self.nacelle_sections_layout.count(), self.delete_nacelle_section, section))

        self.name_line_edit.setText(data["name"])
        self.index = index
