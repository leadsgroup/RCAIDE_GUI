from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, QLineEdit


from tabs.geometry.frames.energy_network.turbofan_network.fueltanks.fuel_tank_frame import FuelTankFrame
from tabs.geometry.frames.energy_network.turbofan_network.propulsors.propulsor_frame import PropulsorFrame
from widgets.data_entry_widget import DataEntryWidget

import RCAIDE

class FuelLineWidget(QWidget):
    def __init__(self, index, on_delete, data_values=None):
        super(FuelLineWidget, self).__init__()

        self.index = index
        self.data_entry_widget: DataEntryWidget | None = None
        self.on_delete = on_delete

        self.main_section_layout = QVBoxLayout()

        layout = self.create_scroll_layout()

        # Segment Name layout
        self.name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        self.name_layout.addWidget(QLabel("Fuel Line Name: "))
        self.name_layout.addWidget(self.section_name_edit)
        layout.addLayout(self.name_layout)

        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create Fuel Tanks tab
        self.fuel_tank_frame = FuelTankFrame()
        self.tab_widget.addTab(self.fuel_tank_frame, "Fuel Tanks")

        # Create Propulsors tab
        self.propulsor_frame = PropulsorFrame()
        self.tab_widget.addTab(self.propulsor_frame, "Propulsors")

        delete_button = QPushButton("Delete Fuel Line", self)
        delete_button.clicked.connect(self.delete_button_pressed)

        layout.addWidget(delete_button)

        self.setLayout(layout)

        if data_values:
            self.load_data_values(data_values, index)
    
    def create_rcaide_structure(self, propulsors, fuel_tanks):
        fuel_line = RCAIDE.Library.Components.EnergyNetwork.FuelLine()
        for propulsor in propulsors:
            fuel_line.propulsors.append(propulsor)
        
        for fuel_tank in fuel_tanks:
            fuel_line.fuel_tanks.append(fuel_tank)
        
        return fuel_line

    def get_data_values(self):
        """Retrieve the entered data values from both FuelTankFrame and PropulsorFrame."""
        data = {}

        # Get the name of the fuel line
        fuel_line_name = self.section_name_edit.text()
        data["name"] = fuel_line_name

        # Get data values from Fuel Tanks tab
        fuel_tank_data = self.fuel_tank_frame.get_data_values()
        data["fuel tank data"], fuel_tanks = fuel_tank_data

        # Get data values from Propulsors tab
        propulsor_data = self.propulsor_frame.get_data_values()
        data["propulsor data"], propulsors = propulsor_data
        
        fuel_line = self.create_rcaide_structure(propulsors, fuel_tanks)
        return data, fuel_line

    def load_data_values(self, data, index):
        self.index = index
        
        fuel_line_name = data["name"]
        self.section_name_edit.setText(fuel_line_name)
        
        fuel_tank_data = data["fuel tank data"]
        self.fuel_tank_frame.load_data(fuel_tank_data)
        
        propulsor_data = data["propulsor data"]
        self.propulsor_frame.load_data(propulsor_data)        
        

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)

    def create_scroll_layout(self):
        # Create a widget to contain the layoutd
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Set the main layout of the widget
        self.setLayout(layout)

        return layout
