from PyQt6.QtWidgets import *

from tabs.geometry.frames.geometry_frame import GeometryFrame
from utilities import show_popup, Units
from widgets.data_entry_widget import DataEntryWidget

from tabs.geometry.energy_network_widgets.turbofan_widgets.fuelline_widget import FuelLineWidget
from tabs.geometry.energy_network_widgets.turbofan_widgets.propulsors.propulsors_main import PropulsorFrame
from tabs.geometry.energy_network_widgets.turbofan_widgets.fueltanks.fuel_tanks_main import FuelTankFrame

class TurboFanWidget(QWidget, GeometryFrame):
    def __init__(self):
        super(TurboFanWidget, self).__init__()

        self.index = -1
        self.tab_index = -1
        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None
        
        
        self.fuelline_sections_layout = QVBoxLayout()  # Define main_layout here

        #Header
        header_layout = QHBoxLayout()
        
        layout = self.create_scroll_layout()
        
        add_section_button = QPushButton("Add Fuel Line Section", self)
        add_section_button.setMaximumWidth(200) 

        add_section_button.clicked.connect(self.add_fuelline_section)
        header_layout.addWidget(add_section_button)
        
        layout.addLayout(header_layout)

        name_layout = QHBoxLayout()

        layout.addLayout(name_layout)
        
        # Add line above buttons
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")
        
        layout.addWidget(line_bar)

        layout.addLayout(self.fuelline_sections_layout)
        

    def add_fuelline_section(self):
        self.fuelline_sections_layout.addWidget(
            FuelLineWidget(self.fuelline_sections_layout.count(), self.on_delete_button_pressed))

    def get_data_values(self):
        # Collect data from fuel line widgets
        additional_data = []
        for index in range(self.fuelline_sections_layout.count()):
            widget = self.fuelline_sections_layout.itemAt(index).widget()
            additional_data.append(widget.get_data_values())

        return additional_data

    def on_delete_button_pressed(self, index):
        self.fuelline_sections_layout.itemAt(index).widget().deleteLater()
        self.fuelline_sections_layout.removeWidget(self.fuelline_sections_layout.itemAt(index).widget())
        self.fuelline_sections_layout.update()
        print("Deleted Fuel Line at Index:", index)

        for i in range(index, self.fuelline_sections_layout.count()):
            self.fuelline_sections_layout.itemAt(i).widget().index = i
            print("Updated Index:", i)
    
    
    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content
    
        # Set the main layout of the widget
        self.setLayout(layout)
    
        return layout