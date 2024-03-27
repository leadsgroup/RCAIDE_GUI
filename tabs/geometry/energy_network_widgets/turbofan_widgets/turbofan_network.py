from PyQt6.QtWidgets import *
from tabs.geometry.energy_network_widgets.turbofan_widgets.propulsors_widget import PropulsorWidget
from tabs.geometry.energy_network_widgets.turbofan_widgets.fuel_tanks_widget import FuelTankWidget


class TurboFanWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        heading_label = QLabel("<b>TurboFan Network</b>")
        layout.addWidget(heading_label)

        # Create a tab widget
        tab_widget = QTabWidget()


        # Determine appropriate values for index and on_delete
        fueltank_index = 0  # Adjust this according to your requirements
        fueltank_on_delete = None  # You may need to define a deletion handler function here
    
        # Create an instance of PropulsorWidget with appropriate arguments
        fueltank_widget = FuelTankWidget(fueltank_index, fueltank_on_delete)
        tab_widget.addTab(fueltank_widget, "Propulsors")
        layout.addWidget(tab_widget)
        

        # Determine appropriate values for index and on_delete
        propulsor_index = 0  # Adjust this according to your requirements
        propulsor_on_delete = None  # You may need to define a deletion handler function here
    
        # Create an instance of PropulsorWidget with appropriate arguments
        propulsors_widget = PropulsorWidget(propulsor_index, propulsor_on_delete)
        tab_widget.addTab(propulsors_widget, "Propulsors")
        layout.addWidget(tab_widget)

        # Add tabs to the tab widget
        tab_widget.addTab(fueltank_widget, "Fuel Tanks")
        tab_widget.addTab(propulsors_widget, "Propulsors")

        layout.addWidget(tab_widget)

        # Add more widgets or functionality as needed

        # Create a QHBoxLayout to contain the buttons
        delete_button_layout = QHBoxLayout()
        add_button_layout = QHBoxLayout()
        
    
        save_data_button = QPushButton("Add Fuel Line", self)
        #save_data_button.clicked.connect(self.save_data)
        add_button_layout.addWidget(save_data_button)
    
    
    
        new_energy_network_structure_button = QPushButton("Delete Fuel Line", self)
        #new_energy_network_structure_button.clicked.connect(self.create_new_structure)
        delete_button_layout.addWidget(new_energy_network_structure_button)
    
    
        # Add the button layout to the main layout
        layout.addLayout(delete_button_layout)
        layout.addLayout(add_button_layout)
        self.setLayout(layout)
