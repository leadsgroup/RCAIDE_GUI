# RCAIDE_GUI/tabs/geometry/frames/cargo_bays/cargo_bay_frame.py
# 
# Created:  Dec 2025, M. Clarke 

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
# RCAIDE imports   
import RCAIDE

# PyQT imports  
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QScrollArea

# RCAIDE GUI imports  
from tabs.geometry.frames        import GeometryFrame 
from utilities import show_popup, create_line_bar, set_data, Units, create_scroll_area, clear_layout
from widgets import DataEntryWidget

# ---------------------------------------------------------------------------------------------------------------------- 
#  Cargo Bay Frame 
# ----------------------------------------------------------------------------------------------------------------------
class CargoBayFrame(GeometryFrame):
    # List of data labels
    data_units_labels = [
        ("Length", Units.Unitless, "length"),
        ("Width", Units.Unitless, "width"),
        ("Height", Units.Length, "height"),
        ("Cargo Mass", Units.Mass, "cargo.mass_properties.mass"), 
        ("Baggage Mass", Units.Mass, "baggage.mass_properties.mass"), 
        ("Container Mass", Units.Mass, "container.mass_properties.mass"), 
        ("Center of Gravity", Units.Position, "mass_properties.center_of_gravity"),
        ("Origin", Units.Position, "origin"),
    ]
 
    def __init__(self):
        """Create a frame for entering cargo bay data."""
        super(CargoBayFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        create_scroll_area(self)

        assert self.main_layout is not None
        self.main_layout.addWidget(QLabel("<b>Cargo Bays</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.index = -1

        self.add_name_layout()

        # Add the data entry widget to the main layout
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

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self):
        """Add the save, delete, and new buttons to the layout.""" 
        save_button = QPushButton("Save Data", self)
        save_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        delete_button = QPushButton("Delete Data", self)
        delete_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        new_button = QPushButton("New Cargo Bay", self)
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
        entered_data, cargo_bay = self.get_data_values()
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(
                    tab_index=self.tab_index, index=self.index, data=entered_data)
                return
            else:
                self.index = self.save_function(
                    tab_index=self.tab_index, vehicle_component=cargo_bay, data=entered_data, new=True)

            show_popup("Data Saved!", self)
        else:
            print("No save function set.") 

    # TODO: Implement proper deletion of data
    def delete_data(self):
        pass

    def create_new_structure(self):
        """Create a new cargo bay structure."""
        # Clear the main data values
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        self.data_entry_widget.clear_values()
        self.name_line_edit.clear() 

    def create_rcaide_structure(self):
        assert self.data_entry_widget is not None
        data = self.data_entry_widget.get_values_si()
        cargo_bay = RCAIDE.Library.Components.Cargo_Bays.Cargo_Bay()
        for data_unit_label in self.data_units_labels:
            rcaide_label = data_unit_label[-1]
            user_label = data_unit_label[0]
            set_data(cargo_bay, rcaide_label, data[user_label][0])
          
        return cargo_bay

    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        assert self.data_entry_widget is not None
        data = self.data_entry_widget.get_values()
        cargo_bay = self.create_rcaide_structure() 

        assert self.name_line_edit is not None
        data["name"] = self.name_line_edit.text()
        return data, cargo_bay

    def load_data(self, data, index):
        """Load the data into the widgets. 

        Args:
            data: The data to be loaded into the widgets.
            index: The index of the data in the list.
        """
        assert self.data_entry_widget is not None
        self.data_entry_widget.load_data(data) 

        assert self.name_line_edit is not None
        self.name_line_edit.setText(data["name"])
        self.index = index
