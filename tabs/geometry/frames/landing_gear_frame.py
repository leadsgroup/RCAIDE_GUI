import RCAIDE
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout,
    QSpacerItem, QSizePolicy, QLabel
)
from PyQt6.QtCore import QSize
from tabs.geometry.frames import GeometryFrame
from utilities import show_popup, create_line_bar, set_data, Units
from widgets import DataEntryWidget
from widgets.collapsible_section import CollapsibleSection

class LandingGearFrame(GeometryFrame):
    # List of data labels
    data_units_labels = [
        ("Main Tire Diameter", Units.Length, "main_tire_diameter"),
        ("Nose Tire Diameter", Units.Length, "nose_tire_diameter"),
        ("Main Strut Length", Units.Length, "main_strut_length"),
        ("Nose Strut Length", Units.Length, "nose_strut_length"),
        ("Main Units", Units.Count, "main_units"),
        ("Nose Units", Units.Count, "nose_units"),
        ("Main Wheels", Units.Count, "main_wheels"),
        ("Nose Wheels", Units.Count, "nose_wheels")
    ]

    def __init__(self):
        super(LandingGearFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        # Main layout for the frame
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Content widget 
        landing_gear_content_widget = QWidget()
        self.content_layout = QVBoxLayout(landing_gear_content_widget)

        # Populate the content layout
        #self.content_layout.addWidget(create_line_bar())
        self.add_name_layout(self.content_layout)

        # Add the data entry widget to the content layout
        self.data_entry_widget = DataEntryWidget(self.data_units_labels)
        self.content_layout.addWidget(self.data_entry_widget)
        self.content_layout.addWidget(create_line_bar())

        # Add buttons layout
        self.add_buttons_layout(self.content_layout)

        # Add a spacer to enable scrolling
        self.content_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Create a collapsible section with scrollability
        collapsible_section = CollapsibleSection("Landing Gear", landing_gear_content_widget)
        main_layout.addWidget(collapsible_section)

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

    def add_buttons_layout(self, layout):
        """
        Add the save, delete, and new buttons to the specified layout.
        """
        save_button = QPushButton("Save Data", self)
        delete_button = QPushButton("Delete Data", self)
        new_button = QPushButton("New Landing Gear Structure", self)

        save_button.clicked.connect(self.save_data)
        delete_button.clicked.connect(self.delete_data)
        new_button.clicked.connect(self.create_new_structure)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(new_button)

        layout.addLayout(buttons_layout)

    # noinspection DuplicatedCode
    def save_data(self):
        """
        Call the save function and pass the entered data to it.
        """
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
        else:
            print("No save function set.")

    # TODO: Implement proper deletion of data
    def delete_data(self):
        pass

    def create_new_structure(self):
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        self.data_entry_widget.clear_values()
        self.name_line_edit.clear()
        self.index = -1

    def create_rcaide_structure(self):
        data = self.data_entry_widget.get_values_si()
        data["name"] = self.name_line_edit.text()
        landing_gear = RCAIDE.Library.Components.Landing_Gear.Landing_Gear()
        landing_gear.tag = data["name"]
        for data_unit_label in self.data_units_labels:
            rcaide_label = data_unit_label[-1]
            user_label = data_unit_label[0]
            set_data(landing_gear, rcaide_label, data[user_label][0])

        return landing_gear

    def get_data_values(self):
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        data = self.data_entry_widget.get_values()
        data["name"] = self.name_line_edit.text()
        landing_gear = self.create_rcaide_structure()
        return data, landing_gear

    def load_data(self, data, index):
        assert self.data_entry_widget is not None and self.name_line_edit is not None
        self.data_entry_widget.load_data(data)
        self.name_line_edit.setText(data["name"])
        self.index = index