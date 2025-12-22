# RCAIDE_GUI/tabs/geometry/frames/wings.py
# 
# Created:  Dec 2025, M. Clarke 

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
 # RCAIDE imports 
import RCAIDE

# PyQT Imports 
from PyQt6.QtCore import Qt 
from PyQt6.QtWidgets import QWidget, QPushButton, QLineEdit, QSizePolicy, QVBoxLayout,\
  QHBoxLayout, QLabel, QFrame, QScrollArea, QSpacerItem, QComboBox
 
# RCAIDE GUI imports 
from tabs.geometry.frames import GeometryFrame
from tabs.geometry.widgets import WingCSWidget, WingSectionWidget, CabinWidget
from utilities import show_popup, create_line_bar, Units, create_scroll_area, set_data, clear_layout
from widgets import DataEntryWidget

# ---------------------------------------------------------------------------------------------------------------------- 
#  Wing Frame 
# ----------------------------------------------------------------------------------------------------------------------
class WingsFrame(GeometryFrame):
    def __init__(self):
        """Create a frame for entering wing data."""
        super(WingsFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        self.cabin_widgets = []
        self.side_cabin_widgets = []

        create_scroll_area(self)

        assert self.main_layout is not None
        self.main_layout.addWidget(QLabel("<b>Wings</b>"))
        self.main_layout.addWidget(create_line_bar())
 
        self.add_name_layout()
        self.add_wing_type()        

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

        self.cabins_layout = QVBoxLayout()
        self.main_layout.addLayout(self.cabins_layout)

        self.side_cabins_layout = QVBoxLayout()
        self.main_layout.addLayout(self.side_cabins_layout)

        self.main_layout.addWidget(create_line_bar())

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
        

    def add_wing_type(self):
        landing_gear_type_label = QLabel("Wing Type: ")
        wing_type_layout = QHBoxLayout()
        spacer_left = QSpacerItem(
            50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(
            200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        wing_type_layout.addItem(spacer_left)
        wing_type_layout.addWidget(landing_gear_type_label)
        self.wing_type_combo = QComboBox()
        self.wing_type_combo.addItems(["Select Wing Type", "All Moving Surface", "Blended Wing Body", "Horizontal Tail", "Main Wing", "Stabilator", "Vertical Tail","Vertical Tail All Moving",  "Wing"])
        self.wing_type_combo.setFixedWidth(600)
        wing_type_layout.addWidget(self.wing_type_combo, alignment=Qt.AlignmentFlag.AlignCenter)
        wing_type_layout.addItem(spacer_right)

        assert self.main_layout is not None
        self.main_layout.addLayout(wing_type_layout)        

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self):
        """Add the save, delete, and new buttons to the layout."""
        new_section_button = QPushButton("Add Wing Segment", self)
        new_section_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        new_cs_button = QPushButton("Add Control Surface", self)
        new_cs_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        new_cabin_button = QPushButton("Add Cabin", self)
        new_cabin_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        new_side_cabin_button = QPushButton("Add Side Cabin", self)
        new_side_cabin_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        save_button = QPushButton("Save Data", self)
        save_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        delete_button = QPushButton("Delete Data", self)
        delete_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        new_button = QPushButton("New Wing Structure", self)
        new_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")

        new_section_button.clicked.connect(self.add_wing_section)
        new_cs_button.clicked.connect(self.add_control_surface)
        new_cabin_button.clicked.connect(self.add_regular_cabin)
        new_side_cabin_button.clicked.connect(self.add_side_cabin)
        save_button.clicked.connect(self.save_data)
        delete_button.clicked.connect(self.delete_data)
        new_button.clicked.connect(self.create_new_structure)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(new_section_button)
        buttons_layout.addWidget(new_cs_button)
        buttons_layout.addWidget(new_cabin_button)
        buttons_layout.addWidget(new_side_cabin_button)
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

    def add_regular_cabin(self, data=None):
        widget = CabinWidget(len(self.cabin_widgets), self.delete_regular_cabin, data, cabin_type="Regular")
        self.cabin_widgets.append(widget)
        self.cabins_layout.addWidget(widget)
    
    def delete_regular_cabin(self, index):
        if 0 <= index < len(self.cabin_widgets):
            widget = self.cabin_widgets[index]
            self.cabins_layout.removeWidget(widget)
            widget.deleteLater()
            self.cabin_widgets.pop(index)
            for i in range(index, len(self.cabin_widgets)):
                self.cabin_widgets[i].index = i

    def add_side_cabin(self, data=None):
        widget = CabinWidget(len(self.side_cabin_widgets), self.delete_side_cabin, data, cabin_type="Side")
        self.side_cabin_widgets.append(widget)
        self.side_cabins_layout.addWidget(widget)

    def delete_side_cabin(self, index):
        if 0 <= index < len(self.side_cabin_widgets):
            widget = self.side_cabin_widgets[index]
            self.side_cabins_layout.removeWidget(widget)
            widget.deleteLater()
            self.side_cabin_widgets.pop(index)
            for i in range(index, len(self.side_cabin_widgets)):
                self.side_cabin_widgets[i].index = i

    # TODO: Implement proper deletion of data
    def delete_data(self):
        pass

    def create_new_structure(self):
        """Create a new wing structure."""
        # # Clear the main data values
        # assert self.data_entry_widget is not None and self.name_line_edit is not None
        self.data_entry_widget.clear_values()
        self.name_line_edit.clear()
        clear_layout(self.wing_sections_layout)
        clear_layout(self.wing_cs_layout)
        clear_layout(self.cabins_layout)
        self.cabin_widgets.clear()
        clear_layout(self.side_cabins_layout)
        self.side_cabin_widgets.clear()

        # # Clear the wing sections
        # for i in range(self.wing_sections_layout.count()):
        #     item = self.wing_sections_layout.itemAt(i)
        #     assert item is not None
        #     widget = item.widget()
        #     assert widget is not None and isinstance(widget, WingSectionWidget)
        #     widget.deleteLater()

        # self.wing_sections_layout.update()

        # # Clear the control surfaces
        # for i in range(self.wing_cs_layout.count()):
        #     item = self.wing_cs_layout.itemAt(i)
        #     assert item is not None
        #     widget = item.widget()
        #     assert widget is not None and isinstance(widget, WingCSWidget)

        #     widget.deleteLater()
        # self.wing_cs_layout.update()


        self.index = -1

    def create_rcaide_structure(self):
        assert self.data_entry_widget is not None
        data = self.data_entry_widget.get_values_si()
        data["name"] = self.name_line_edit.text() 

        selected_wing_type = self.wing_type_combo.currentText()
        if selected_wing_type == "All Moving Surface": 
            wing = RCAIDE.Library.Components.Wings.All_Moving_Surface()
        elif selected_wing_type ==  "Blended Wing Body": 
            wing = RCAIDE.Library.Components.Wings.Blended_Wing_Body()
        elif selected_wing_type == "Horizontal Tail": 
            wing = RCAIDE.Library.Components.Wings.Horizontal_Tail()
        elif selected_wing_type == "Main Wing": 
            wing = RCAIDE.Library.Components.Wings.Main_Wing()
        elif selected_wing_type == "Stabilator": 
            wing = RCAIDE.Library.Components.Wings.Stabilator()
        elif selected_wing_type == "Vertical Tail": 
            wing = RCAIDE.Library.Components.Wings.Vertical_Tail()
        elif selected_wing_type == "Vertical Tail All Moving": 
            wing = RCAIDE.Library.Components.Wings.Vertical_Tail_All_Moving()
        elif selected_wing_type == "Wing": 
            wing = RCAIDE.Library.Components.Wings.Wing() 

        # assign wing name 
        wing.tag = data["name"]
        
        # assign wing properties 
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
        
        data["cabins"] = []
        if not hasattr(wing, "cabins"):
            wing.cabins = RCAIDE.Library.Components.Fuselages.Cabins.Cabin.Container()
        for widget in self.cabin_widgets:
            cabin_data, cabin_object = widget.get_data_values()
            data["cabins"].append(cabin_data)
            wing.cabins.append_cabin(cabin_object)
        
        data["side_cabins"] = []
        if not hasattr(wing, "side_cabins"):
            wing.side_cabins = RCAIDE.Library.Components.Fuselages.Cabins.Side_Cabin.Container()
        for widget in self.side_cabin_widgets:
            cabin_data, cabin_object = widget.get_data_values()
            data["side_cabins"].append(cabin_data)
            wing.side_cabins.append_side_cabin(cabin_object)
            

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
        clear_layout(self.cabins_layout)
        clear_layout(self.side_cabins_layout)
        
        for section in data["sections"]:
            self.wing_sections_layout.addWidget(WingSectionWidget(
                self.wing_sections_layout.count(), self.delete_wing_section, section))

        for section in data["control_surfaces"]:
            self.wing_cs_layout.addWidget(WingCSWidget(
                self.wing_cs_layout.count(), self.delete_control_surface, section))
            
        if "cabins" in data:
            for cabin_data in data["cabins"]:
                self.add_regular_cabin(cabin_data)
        
        if "side_cabins" in data:
            for cabin_data in data["side_cabins"]:
                self.add_side_cabin(cabin_data)

        self.name_line_edit.setText(data["name"])
        self.index = index
