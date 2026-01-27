# RCAIDE_GUI/tabs/geometry/frames/landing_gears/landing_gear_frame.py
# 
# Created:  Dec 2025, M. Clarke 

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
# RCAIDE imports 
import RCAIDE

# PyQT imports 
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QPushButton, QLineEdit, QSizePolicy, QVBoxLayout,\
     QHBoxLayout, QLabel, QFrame, QScrollArea, QSpacerItem, QComboBox

# RCAIDE GUI imports 
from tabs.geometry.frames import GeometryFrame 
from utilities import set_data, show_popup, create_line_bar, Units, create_scroll_area, clear_layout
from widgets import DataEntryWidget
 
# ---------------------------------------------------------------------------------------------------------------------- 
#  Landing Gear Frame 
# ----------------------------------------------------------------------------------------------------------------------
class LandingGearFrame(GeometryFrame):

    # List of data labels
    data_units_labels = [
        ("Tire Diameter", Units.Length, "tire_diameter"),
        ("Rim Diameter", Units.Length,  "rim_diameter"),
        ("Tire Width", Units.Length, "tire_width"),
        ("Strut Length", Units.Length, "strut_length"), 
        ("Origin", Units.Position, "origin"),
        ("Wheels", Units.Count, "wheels"), 
        ("Number of Gear Types in Tandem", Units.Count, "number_of_gear_types_in_tandem"), 
        ("Number of Wheels in Gear Type", Units.Count, "number_of_wheels_in_gear_type"),  
        ("X-Z Plane Symmetric", Units.Boolean, "xz_plane_symmetric"),
    ]
    
    def __init__(self):
        """Create a frame for entering landing gear data."""
        super(LandingGearFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        create_scroll_area(self)

        assert self.main_layout is not None
        self.main_layout.addWidget(QLabel("<b>Landing Gears</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.add_name_layout()
        self.add_landing_gear_type()

        # Add the data entry widget to the home layout
        self.data_entry_widget = DataEntryWidget(self.data_units_labels)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addWidget(create_line_bar())

        self.add_buttons_layout()

        # Adds scroll function
        self.main_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def add_name_layout(self):
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

        assert self.main_layout is not None
        self.main_layout.addLayout(name_layout)
    
    def add_landing_gear_type(self):
        landing_gear_type_label = QLabel("Landing Gear Type: ")
        gear_type_layout = QHBoxLayout()
        spacer_left = QSpacerItem(
            50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(
            200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        gear_type_layout.addItem(spacer_left)
        gear_type_layout.addWidget(landing_gear_type_label)
        self.landing_gear_type_combo = QComboBox()
        self.landing_gear_type_combo.addItems(["General Gear","Nose Gear", "Main Gear"])
        self.landing_gear_type_combo.setFixedWidth(600)
        gear_type_layout.addWidget(self.landing_gear_type_combo, alignment=Qt.AlignmentFlag.AlignCenter)
        gear_type_layout.addItem(spacer_right)

        assert self.main_layout is not None
        self.main_layout.addLayout(gear_type_layout)

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self):
        """Add the save, delete, and new buttons to the layout."""
        save_button = QPushButton("Save Data", self)
        save_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        delete_button = QPushButton("Delete Data", self)
        delete_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        new_button = QPushButton("New Landing Gear Structure", self)
        new_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")

        save_button.clicked.connect(self.save_data)
        delete_button.clicked.connect(self.delete_data)
        new_button.clicked.connect(self.create_new_structure)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(new_button)

        assert self.main_layout is not None
        self.main_layout.addLayout(buttons_layout)

    # noinspection DuplicatedCode
    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data, landing_gear = self.get_data_values()
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(
                    tab_index=self.tab_index, index=self.index, data=entered_data)
                return
            else:
                self.index = self.save_function(
                    tab_index=self.tab_index, vehicle_component=landing_gear, data=entered_data, new=True)

            show_popup("Data Saved!", self)

    # TODO: Implement proper deletion of data
    def delete_data(self):
        pass

    def create_new_structure(self):
        """Create a new Landing Gear structure."""
        # Clear the main data values
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        self.data_entry_widget.clear_values()
        self.name_line_edit.clear()
        self.index = -1

    def create_rcaide_structure(self):
        data = self.data_entry_widget.get_values_si()
        data["name"] = self.name_line_edit.text() 
        selected_landing_gear_type = self.landing_gear_type_combo.currentText()
        if selected_landing_gear_type == "General Gear": 
            landing_gear = RCAIDE.Library.Components.Landing_Gear.Landing_Gear()
        elif selected_landing_gear_type == "Nose Gear": 
            landing_gear = RCAIDE.Library.Components.Landing_Gear.Nose_Landing_Gear()
        elif selected_landing_gear_type == "Main Gear": 
            landing_gear = RCAIDE.Library.Components.Landing_Gear.Main_Landing_Gear()
        landing_gear.tag = data["name"]
        for data_unit_label in self.data_units_labels:
            rcaide_label = data_unit_label[-1]
            user_label = data_unit_label[0]
            set_data(landing_gear, rcaide_label, data[user_label][0]) 
        return landing_gear

    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        data = self.data_entry_widget.get_values()
        data["name"] = self.name_line_edit.text()
        data["landing_gear_type"] = self.landing_gear_type_combo.currentText()
        landing_gear = self.create_rcaide_structure()
        return data, landing_gear

    def load_data(self, data, index):
        """Load the data into the widgets.

        Args:
            data: The data to be loaded into the widgets.
            index: The index of the data in the list.
        """
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        self.data_entry_widget.load_data(data)

        if "landing_gear_type" in data:
            self.landing_gear_type_combo.setCurrentText(data["landing_gear_type"])
        else:
            self.landing_gear_type_combo.setCurrentIndex(0)        

        self.name_line_edit.setText(data["name"])
        self.index = index
