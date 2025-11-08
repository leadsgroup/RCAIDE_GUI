import RCAIDE
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QTabWidget

from tabs.geometry.frames.energy_network import EnergyNetworkWidget
from tabs.geometry.frames.energy_network.turbofan_network.widgets import FuelLineWidget, TankSelectorWidget
from widgets import DataEntryWidget


class TurbofanNetworkWidget(QWidget, EnergyNetworkWidget):
    def __init__(self):
        super(TurbofanNetworkWidget, self).__init__()

        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        self.fuellines_layout = QVBoxLayout()  # Define main_layout here
        self.fuellines_layout.setContentsMargins(0, 0, 0, 0)

        self.tank_selector_data = None

        # Header
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
        layout.addLayout(self.fuellines_layout)

        update_selector_button = QPushButton("Update Fuel Tank Selector")
        update_selector_button.clicked.connect(self.update_fuel_selector)
        layout.addWidget(update_selector_button)

        self.fuel_tank_selector = QTabWidget()
        self.fuel_tank_selector.setTabPosition(QTabWidget.TabPosition.North)
        layout.addWidget(self.fuel_tank_selector)

    def add_fuelline_section(self):
        self.fuellines_layout.addWidget(
            FuelLineWidget(self.fuellines_layout.count(), self.on_delete_button_pressed))

    def update_fuel_selector(self, data=None):
        self.fuel_tank_selector.clear()
        if data is None or isinstance(data, bool):
            data, _ = self.get_data_values(just_data=True)

        self.tank_selector_data = data
        for line_data in data:
            for propulsor_data in line_data["propulsor data"]:
                tank_names = [tank["Segment Name"]
                              for tank in line_data["fuel tank data"]]
                propulsor_name = propulsor_data["propulsor name"]
                self.fuel_tank_selector.addTab(TankSelectorWidget(
                    tank_names, propulsor_name), propulsor_name)

    def load_data_values(self, data):
        for i in reversed(range(self.fuellines_layout.count())):
            widget_item = self.fuellines_layout.itemAt(i)
            assert widget_item is not None
            widget = widget_item.widget()
            assert widget is not None

            self.fuellines_layout.removeWidget(widget)
            widget.deleteLater()

        for index, section in enumerate(data):
            self.fuellines_layout.addWidget(
                FuelLineWidget(index, self.on_delete_button_pressed, section))
        
        self.update_fuel_selector(self.get_data_values(just_data=True)[0])

    def get_data_values(self, just_data=False):
        # Collect data from fuel line widgets
        data = []
        lines = []
        for index in range(self.fuellines_layout.count()):
            item = self.fuellines_layout.itemAt(index)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, FuelLineWidget)
            fuelline_data, line, propulsors = widget.get_data_values()
            assert isinstance(line, RCAIDE.Library.Components.Powertrain.Distributors.Fuel_Line)

            data.append(fuelline_data)
            lines.append(line)

        if just_data:
            return data, [], []

        if self.tank_selector_data != data:
            print(self.tank_selector_data)
            print(data)
            print("Tank selector is not updated!")
            return False, False

        for line in lines:
            for propulsor in propulsors:
                assert isinstance(propulsor, RCAIDE.Library.Components.Powertrain.Propulsors.Turbofan)

                for index in range(self.fuel_tank_selector.count()):
                    tank_selector = self.fuel_tank_selector.widget(index)
                    assert isinstance(tank_selector, TankSelectorWidget)
                    if tank_selector.name != propulsor.tag:
                        continue

                    propulsor.active_fuel_tanks = tank_selector.get_selected_tanks() 
                    break

        return data, lines, propulsors

    def on_delete_button_pressed(self, index):
        widget_item = self.fuellines_layout.itemAt(index)
        if widget_item is not None:
            widget = widget_item.widget()
            self.fuellines_layout.removeWidget(widget)
            self.fuellines_layout.update()
            print("Deleted Fuel Line at Index:", index)

            for i in range(index, self.fuellines_layout.count()):
                widget_item = self.fuellines_layout.itemAt(i)
                assert widget_item is not None
                widget = widget_item.widget()
                assert widget is not None and isinstance(
                    widget, FuelLineWidget)

                widget.index = i
                print("Updated Index:", i)

    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        # Set the main layout inside the scroll content
        layout = QVBoxLayout(scroll_content)

        # Set the main layout of the widget
        self.setLayout(layout)
        return layout
