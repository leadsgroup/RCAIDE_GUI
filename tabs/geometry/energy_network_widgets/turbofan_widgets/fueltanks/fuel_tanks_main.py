from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, \
    QSizePolicy, QSpacerItem, QLineEdit

from tabs.geometry.frames.geometry_frame import GeometryFrame

from utilities import show_popup, Units
from widgets.data_entry_widget import DataEntryWidget
from tabs.geometry.energy_network_widgets.turbofan_widgets.fueltanks.fuel_tanks_widget import FuelTankWidget

class FuelTankFrame(QWidget, GeometryFrame):
    def __init__(self):
        super(FuelTankFrame, self).__init__()

        self.index = -1
        self.tab_index = -1
        self.save_function = None
        self.data_entry_widget : DataEntryWidget | None = None


        # List to store data values fuel_tank_ sections
        self.fuel_tank_sections_layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QVBoxLayout()
        #label = QLabel("<u><b>Fuel Tank Frame</b></u>")

        layout = self.create_scroll_layout()

        #header_layout.addWidget(label)
        
        
        # Add fuel_tank_ Section Button at the top
        add_section_button = QPushButton("Add Fuel Tank Segment", self)
        add_section_button.setMaximumWidth(150) 
        add_section_button.clicked.connect(self.add_fuel_tank_section)
        header_layout.addWidget(add_section_button)
        
        
        
        layout.addLayout(header_layout)

        name_layout = QHBoxLayout()

        layout.addLayout(name_layout)


        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Add the layout for additional fuel_tank_ sections to the main layout
        layout.addLayout(self.fuel_tank_sections_layout)

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()


        ## Append All fuel_tank_ Section Data Button
        #append_all_data_button = QPushButton("Save Fuel Line Data", self)
        #append_all_data_button.clicked.connect(self.save_data)
        #button_layout.addWidget(append_all_data_button)


        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def get_data_values(self):


        # Collect data from additional fuel_tank__widget
        additional_data = []
        for index in range(self.fuel_tank_sections_layout.count()):
            widget = self.fuel_tank_sections_layout.itemAt(index).widget()
            additional_data.append(widget.get_data_values())

        #data["sections"] = additional_data
        return additional_data

    def save_data(self):
        """Append the entered data to a list or perform any other action."""
        entered_data = self.get_data_values()

        print("Main fuel_tank_ Data:", entered_data)

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
        while self.fuel_tank_sections_layout.count():
            item = self.fuel_tank_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for section_data in data["sections"]:
            self.fuel_tank_sections_layout.addWidget(FuelTankWidget(
                self.fuel_tank_sections_layout.count(), self.on_delete_button_pressed, section_data))

    def delete_data(self):
        """Delete the entered data or perform any other action."""
        self.data_entry_widget.clear_values()

    def add_fuel_tank_section(self):
        self.fuel_tank_sections_layout.addWidget(
            FuelTankWidget(self.fuel_tank_sections_layout.count(), self.on_delete_button_pressed))

    def on_delete_button_pressed(self, index):
        self.fuel_tank_sections_layout.itemAt(index).widget().deleteLater()
        self.fuel_tank_sections_layout.removeWidget(self.fuel_tank_sections_layout.itemAt(index).widget())
        self.fuel_tank_sections_layout.update()
        print("Deleted fuel_tank_ at Index:", index)

        for i in range(index, self.fuel_tank_sections_layout.count()):
            self.fuel_tank_sections_layout.itemAt(i).widget().index = i
            print("Updated Index:", i)

    def update_units(self, line_edit, unit_combobox):
        pass

    def set_save_function(self, function):
        self.save_function = function

    def set_tab_index(self, index):
        self.tab_index = index

    def create_new_structure(self):
        """Create a new fuel_tank_ structure."""

        # Clear the main data values
        self.data_entry_widget.clear_values()

        # Clear the name line edit
        while self.fuel_tank_sections_layout.count():
            item = self.fuel_tank_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.name_line_edit.clear()
        self.index = -1

    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content
    
        # Set the main layout of the widget
        self.setLayout(layout)
    
        return layout

