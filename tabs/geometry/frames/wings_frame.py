import RCAIDE
from RCAIDE.Library.Methods.Geometry.Planform import wing_planform
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QScrollArea

from tabs.geometry.frames import GeometryFrame
from tabs.geometry.widgets import WingCSWidget, WingSectionWidget
from utilities import show_popup, create_line_bar, Units, create_scroll_area, set_data, clear_layout
from widgets import DataEntryWidget


class WingsFrame(GeometryFrame):
    def __init__(self):
        """Create a frame for entering wing data."""
        super(WingsFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        create_scroll_area(self)

        assert self.main_layout is not None
        self.main_layout.addWidget(QLabel("<b>Wings</b>"))
        self.main_layout.addWidget(create_line_bar())

        # TODO Add extra flags

        self.add_name_layout()

        # List of data labels
        self.data_units_labels = [
            ("Spans Projected", Units.Length, "spans.projected"),
            ("Reference Area", Units.Area, "areas.reference"),
            ("Wetted Area", Units.Area, "areas.wetted"),
            ("Root Chord", Units.Length, "chords.root"),
            ("Tip Chord", Units.Length, "chords.tip"),
            ("Mean Aerodynamic Chord", Units.Length, "chords.mean_aerodynamic"),
            ("Quarter Chord Sweep Angle", Units.Angle, "sweeps.quarter_chord"),
            ("Leading Edge Sweep Angle", Units.Angle, "sweeps.leading_edge"),
            ("Root Chord Twist Angle", Units.Angle, "twists.root"),
            ("Tip Chord Twist Angle", Units.Angle, "twists.tip"),
            ("Taper", Units.Unitless, "taper"),
            ("Dihedral", Units.Angle, "dihedral"),
            ("Aspect Ratio", Units.Unitless, "aspect_ratio"),
            ("Thickness to Chord", Units.Unitless, "thickness_to_chord"),
            ("Aerodynamic Center", Units.Position, "aerodynamic_center"),
            ("Origin", Units.Position, "origin"),
            ("Vertical", Units.Boolean, "vertical"),
            ("X-Y Plane Symmetric", Units.Boolean, "xy_plane_symmetric"),
            ("High Lift", Units.Boolean, "high_lift"),
            ("X-Z Plane Symmetric", Units.Boolean, "xz_plane_symmetric"),
            ("T-Tail", Units.Boolean, "t_tail"),
            ("Y-Z Plane Symmetric", Units.Boolean, "yz_plane_symmetric"),
            ("Dynamic Pressure Ratio", Units.Unitless, "dynamic_pressure_ratio"),
            ("Exposed Root Chord Offset", Units.Unitless,
             "exposed_root_chord_offset")
        ]

        # Add the data entry widget to the main layout
        self.data_entry_widget = DataEntryWidget(self.data_units_labels)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addWidget(create_line_bar())

        # Add the sections layout to the main layout
        self.wing_sections_layout = QVBoxLayout()
        self.main_layout.addLayout(self.wing_sections_layout)

        self.wing_cs_layout = QVBoxLayout()
        self.main_layout.addWidget(create_line_bar())
        # self.main_layout.addWidget(QLabel("Control Surfaces"))
        self.main_layout.addLayout(self.wing_cs_layout)

        self.add_buttons_layout()

        # Adds scroll function
        self.main_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def add_name_layout(self):
        assert self.main_layout is not None

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
        self.main_layout.addLayout(name_layout)

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self):
        """Add the save, delete, and new buttons to the layout."""
        new_section_button = QPushButton("New Wing Segment", self)
        new_cs_button = QPushButton("New Control Surface", self)
        save_button = QPushButton("Save Data", self)
        delete_button = QPushButton("Delete Data", self)
        new_button = QPushButton("New Wing Structure", self)

        new_section_button.clicked.connect(self.add_wing_section)
        new_cs_button.clicked.connect(self.add_control_surface)
        save_button.clicked.connect(self.save_data)
        delete_button.clicked.connect(self.delete_data)
        new_button.clicked.connect(self.create_new_structure)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(new_section_button)
        buttons_layout.addWidget(new_cs_button)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(new_button)

        assert self.main_layout is not None
        self.main_layout.addLayout(buttons_layout)

    # noinspection DuplicatedCode
    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data, wing = self.get_data_values()
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(
                    tab_index=self.tab_index, index=self.index, data=entered_data)
                return
            else:
                self.index = self.save_function(
                    tab_index=self.tab_index, vehicle_component=wing, data=entered_data, new=True)

            show_popup("Data Saved!", self)

    def add_wing_section(self):
        self.wing_sections_layout.addWidget(WingSectionWidget(
            self.wing_sections_layout.count(), self.delete_wing_section))

    def delete_wing_section(self, index):
        item = self.wing_sections_layout.itemAt(index)
        assert item is not None
        widget = item.widget()
        assert widget is not None and isinstance(widget, WingSectionWidget)

        widget.deleteLater()
        self.wing_sections_layout.removeWidget(widget)
        self.wing_sections_layout.update()

        for i in range(index, self.wing_sections_layout.count()):
            item = self.wing_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, WingSectionWidget):
                widget.index = i

    def add_control_surface(self):
        self.wing_cs_layout.addWidget(WingCSWidget(
            self.wing_cs_layout.count(), self.delete_control_surface))

    def delete_control_surface(self, index):
        item = self.wing_cs_layout.itemAt(index)
        assert item is not None
        widget = item.widget()
        assert widget is not None and isinstance(widget, WingCSWidget)

        widget.deleteLater()
        self.wing_cs_layout.removeWidget(widget)
        self.wing_cs_layout.update()

        for i in range(index, self.wing_cs_layout.count()):
            item = self.wing_cs_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, WingCSWidget):
                widget.index = i

    # TODO: Implement proper deletion of data
    def delete_data(self):
        pass

    def create_new_structure(self):
        """Create a new wing structure."""
        # Clear the main data values
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        self.data_entry_widget.clear_values()
        self.name_line_edit.clear()

        # Clear the wing sections
        for i in range(self.wing_sections_layout.count()):
            item = self.wing_sections_layout.itemAt(i)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, WingSectionWidget)
            widget.deleteLater()

        self.wing_sections_layout.update()

        # Clear the control surfaces
        for i in range(self.wing_cs_layout.count()):
            item = self.wing_cs_layout.itemAt(i)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, WingCSWidget)

            widget.deleteLater()
        self.wing_cs_layout.update()

        self.index = -1

    def create_rcaide_structure(self):
        assert self.data_entry_widget is not None
        data = self.data_entry_widget.get_values_si()
        data["name"] = self.name_line_edit.text()

        wing = RCAIDE.Library.Components.Wings.Main_Wing()

        wing.tag = data["name"]

        for data_unit_label in self.data_units_labels:
            rcaide_label = data_unit_label[-1]
            user_label = data_unit_label[0]
            set_data(wing, rcaide_label, data[user_label][0])
        
        wing.aerodynamic_center = data["Aerodynamic Center"][0][0]

        for i in range(self.wing_sections_layout.count()):
            item = self.wing_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, WingSectionWidget):
                _, wing_section = widget.get_data_values()
                wing.append_segment(wing_section)

        for i in range(self.wing_cs_layout.count()):
            item = self.wing_cs_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, WingCSWidget):
                _, cs = widget.get_data_values()
                wing.append_control_surface(cs)

        wing = wing_planform(wing)
        return wing

    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        data = self.data_entry_widget.get_values()
        data["name"] = self.name_line_edit.text()
        wing = self.create_rcaide_structure()

        data["sections"] = []
        for i in range(self.wing_sections_layout.count()):
            item = self.wing_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, WingSectionWidget):
                section_data, wing_section = widget.get_data_values()
                wing.append_segment(wing_section)
                data["sections"].append(section_data)

        data["control_surfaces"] = []
        for i in range(self.wing_cs_layout.count()):
            item = self.wing_cs_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, WingCSWidget):
                cs_data, cs = widget.get_data_values()
                wing.append_control_surface(cs)
                data["control_surfaces"].append(cs_data)

        return data, wing

    def load_data(self, data, index):
        """Load the data into the widgets.

        Args:
            data: The data to be loaded into the widgets.py
            index: The index of the data in the list.
        """
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        self.data_entry_widget.load_data(data)

        clear_layout(self.wing_sections_layout)
        clear_layout(self.wing_cs_layout)
        
        for section in data["sections"]:
            self.wing_sections_layout.addWidget(WingSectionWidget(
                self.wing_sections_layout.count(), self.delete_wing_section, section))

        for section in data["control_surfaces"]:
            self.wing_cs_layout.addWidget(WingCSWidget(
                self.wing_cs_layout.count(), self.delete_control_surface, section))

        self.name_line_edit.setText(data["name"])
        self.index = index
