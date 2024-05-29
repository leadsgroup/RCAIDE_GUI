from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QTabWidget, QPushButton, QLineEdit

from tabs.geometry.frames.energy_network.turbofan_widgets.fueltanks.fuel_tank_frame import FuelTankFrame
from tabs.geometry.frames.energy_network.turbofan_widgets.propulsors.propulsor_frame import PropulsorFrame
from widgets.data_entry_widget import DataEntryWidget


class FuelLineWidget(QWidget):
    def __init__(self, index, on_delete, data_values=None):
        super(FuelLineWidget, self).__init__()

        self.index = index
        self.data_entry_widget: DataEntryWidget | None = None
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
            self.load_data(data_values, index)

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

    def load_data(self, data, index):
        pass

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
