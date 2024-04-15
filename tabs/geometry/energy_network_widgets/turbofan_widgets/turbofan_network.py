from PyQt6.QtWidgets import *
from tabs.geometry.energy_network_widgets.turbofan_widgets.fuelline_widget import FuelLineWidget
from tabs.geometry.energy_network_widgets.turbofan_widgets.propulsors.propulsors_main import PropulsorFrame
from tabs.geometry.energy_network_widgets.turbofan_widgets.fueltanks.fuel_tanks_main import FuelTankFrame

class TurboFanWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.fuel_line_widgets = []
        self.propulsor_widget = PropulsorFrame()  
        self.fuel_tank_widget = FuelTankFrame()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        #Header
        header_layout = QHBoxLayout()
        #header_label = QLabel("<u><b>TurboFan Network</b></u>")
        #header_layout.addWidget(header_label)
        main_layout.addLayout(header_layout)

        # Line bar
        #line_bar = QFrame()
        #line_bar.setFrameShape(QFrame.Shape.HLine)
        #line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        #main_layout.addWidget(line_bar)

        # Initial fuel line section
        self.add_fuelline_section()

        # Add line above buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")
        main_layout.addWidget(line_above_buttons)

        # Buttons layout
        button_layout = QHBoxLayout()

        add_section_button = QPushButton("Add Fuel Line Section", self)
        add_section_button.clicked.connect(self.add_fuelline_section)
        button_layout.addWidget(add_section_button)

        main_layout.addLayout(button_layout)
        
        

    def add_fuelline_section(self):
        fuel_line_widget = FuelLineWidget(len(self.fuel_line_widgets), self.on_delete_button_pressed)
        self.fuel_line_widgets.append(fuel_line_widget)
        self.layout().insertWidget(self.layout().count() - 2, fuel_line_widget)

    def get_data_values(self):
        """Retrieve the entered data values from the widgets."""
        data = {
            "propulsor_data": self.propulsor_widget.get_data_values(),  # Access PropulsorWidget instance
            "fuel_tank_data": self.fuel_tank_widget.get_data_values(),  # Access FuelTankWidget instance
            "fuel_line_data": []
        }

        for fuel_line_widget in self.fuel_line_widgets:
            data["fuel_line_data"].append(fuel_line_widget.get_data_values())

        return data

    def on_delete_button_pressed(self, index):
        if 0 <= index < len(self.fuel_line_widgets):
            fuel_line_widget = self.fuel_line_widgets.pop(index)
            fuel_line_widget.setParent(None)
            del fuel_line_widget

            # Reset indexes for remaining fuel line widgets
            for i, widget in enumerate(self.fuel_line_widgets):
                widget.index = i
