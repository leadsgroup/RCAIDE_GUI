from turtle import clear
import RCAIDE
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, QPushButton, QLineEdit
from tabs.geometry.frames import GeometryFrame
from tabs.geometry.widgets import NacelleSectionWidget
from utilities import set_data, show_popup, create_line_bar, Units, clear_layout, create_scroll_area
from widgets import DataEntryWidget
from widgets.collapsible_section import CollapsibleSection

class NacelleFrame(GeometryFrame):
    def __init__(self):
        """Create a frame for entering nacelle data."""
        super(NacelleFrame, self).__init__()

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        nacelle_content_widget = QWidget()
        self.content_layout = QVBoxLayout(nacelle_content_widget)

        self.add_name_layout(self.content_layout)

        # List of data labels
        self.data_units_labels = [
            ("Length", Units.Length, "length"),
            ("Inlet Diameter", Units.Length, "inlet_diameter"),
            ("Diameter", Units.Length, "diameter"),
            ("Origin", Units.Position, "origin"),
            ("Wetted Area", Units.Area, "areas.wetted"),
            ("Flow Through", Units.Boolean, "flow_through"),
            # ("Airfoil Flag", Units.Boolean),
            # ("Airfoil Coordinate File", Units.Unitless)
        ]

        # Add the data entry widget to the content layout
        self.data_entry_widget: DataEntryWidget = DataEntryWidget(
            self.data_units_labels)

        self.content_layout.addWidget(self.data_entry_widget)
        self.content_layout.addWidget(create_line_bar())

        # Add the secctions layout to the content layout
        self.nacelle_sections_layout = QVBoxLayout()
        self.content_layout.addLayout(self.nacelle_sections_layout)

        self.add_buttons_layout(self.content_layout)

        # Adds scroll function
        self.content_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        collapsible = CollapsibleSection("Nacelle", nacelle_content_widget)
        main_layout.addWidget(collapsible)

    def add_name_layout(self,layout):
        name_layout = QHBoxLayout()
        spacer_left = QSpacerItem(
            50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(
            200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_line_edit = QLineEdit(self)
        name_layout.addItem(spacer_left)
        name_layout.addWidget(QLabel("Name: "))
        name_layout.addWidget(self.name_line_edit)
        name_layout.addItem(spacer_right)

        layout.addLayout(name_layout)

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self,layout):
        """Add the save, delete, and new buttons to the layout."""
        #assert self.main_layout is not None
        
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
        #self.main_layout.addLayout(buttons_layout)
        layout.addLayout(buttons_layout)

    # noinspection DuplicatedCode
    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data, v_comp = self.get_data_values()
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(
                    tab_index=self.tab_index, index=self.index, data=entered_data)
                return
            else:
                self.index = self.save_function(
                    tab_index=self.tab_index, vehicle_component=v_comp, data=entered_data, new=True)

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

    def create_rcaide_structure(self):
        """Create a nacelle structure from the given data."""
        data = self.data_entry_widget.get_values_si()
        data["name"] = self.name_line_edit.text()
        nacelle = RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle()
        for data_unit_label in self.data_units_labels:
            user_label = data_unit_label[0]
            rcaide_label = data_unit_label[-1]
            set_data(nacelle, rcaide_label, data[user_label][0])
                
        nacelle_airfoil = RCAIDE.Library.Components.Airfoils.NACA_4_Series_Airfoil()
        nacelle_airfoil.NACA_4_Series_code = '2410'
        nacelle.append_airfoil(nacelle_airfoil)

        for i in range(self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, NacelleSectionWidget):
                _, segment = widget.get_data_values()
                nacelle.append_segment(segment)

        nacelle.tag = data["name"]
        return nacelle

    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data_si["name"] = self.name_line_edit.text()

        nacelle = self.create_rcaide_structure()

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
        
        while self.nacelle_sections_layout.count():
            item = self.nacelle_sections_layout.takeAt(0)
            assert item is not None
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        clear_layout(self.nacelle_sections_layout)
        self.name_line_edit.setText(data["name"])
        self.index = index