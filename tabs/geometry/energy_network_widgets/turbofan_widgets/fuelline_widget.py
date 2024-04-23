import os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from utilities import show_popup, Units
from widgets.unit_picker_widget import UnitPickerWidget
from widgets.data_entry_widget import DataEntryWidget
from tabs.geometry.frames.geometry_frame import GeometryFrame

from tabs.geometry.energy_network_widgets.turbofan_widgets.propulsors.propulsors_main import PropulsorFrame
from tabs.geometry.energy_network_widgets.turbofan_widgets.fueltanks.fuel_tanks_main import FuelTankFrame

class FuelLineWidget(QWidget):
    def __init__(self, index, on_delete, data_values=None):
        super(FuelLineWidget, self).__init__()

        self.index = -1
        self.tab_index = -1
        self.save_function = None
        self.data_entry_widget : DataEntryWidget | None = None
        self.on_delete = on_delete
        
        
        self.main_section_layout = QVBoxLayout()
        
        layout = self.create_scroll_layout()
                
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey; border: 2px solid grey;")
        
        layout.addWidget(line_bar)

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
        fuel_tank_widget = FuelTankFrame()
        self.tab_widget.addTab(fuel_tank_widget, "Fuel Tanks")

        # Create Propulsors tab
        propulsor_widget = PropulsorFrame()
        self.tab_widget.addTab(propulsor_widget, "Propulsors")

        delete_button = QPushButton("Delete Fuel Line Segment", self)
        delete_button.clicked.connect(self.delete_button_pressed)

        layout.addWidget(delete_button)

        self.setLayout(layout)

        if data_values:
            self.load_data_values(data_values)



    def get_data_values(self):
        """Retrieve the entered data values from both FuelTankFrame and PropulsorFrame."""
        data_values = {}

        # Get the name of the fuel line
        fuel_line_name = self.section_name_edit.text()
        data_values["name"] = fuel_line_name

        # Get data values from Fuel Tanks tab
        fuel_tank_widget = self.tab_widget.widget(0)
        fuel_tank_data = fuel_tank_widget.get_data_values()
        data_values["Fuel Tank Data"] = fuel_tank_data

        # Get data values from Propulsors tab
        propulsor_widget = self.tab_widget.widget(1)
        propulsor_data = propulsor_widget.get_data_values()
        data_values["Propulsor Data"] = propulsor_data

        return data_values


    def save_data(self):
        """Append the entered data to a list or perform any other action."""
        entered_data = self.get_data_values()

        print("Fuel Line Data:", entered_data)

        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(self.tab_index, self.index, entered_data)
                return
            else:
                self.index = self.save_function(self.tab_index, data=entered_data, new=True)

            show_popup("Data Saved!", self)

    def load_data(self, data, index):
        self.data_entry_widget.load_data(data)
        self.name_edit.setText(data["name"])

        # Make sure sections don't already exist
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for section_data in data["Fuel Tank Data"]:
            self.main_layout.addWidget(FuelTankFrame(
                self.main_layout.count(), self.on_delete_button_pressed, section_data))
            
        for section_data in data["Propulsor Data"]:
            self.main_layout.addWidget(PropulsorFrame(
                self.main_layout.count(), self.elementon_delete_button_pressed, section_data))

    def on_delete_button_pressed(self, index):
        self.main_layout.itemAt(index).widget().deleteLater()
        self.main_layout.removeWidget(self.main_layout.itemAt(index).widget())
        self.main_layout.update()
        print("Deleted FuelLine at Index:", index)

        for i in range(index, self.main_layout.count()):
            self.main_layout.itemAt(i).widget().index = i
            print("Updated Index:", i)

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
