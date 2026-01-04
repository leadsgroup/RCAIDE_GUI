# RCAIDE_GUI/tabs/geometry/frames/nacelles/nacelle_frame.py
#
# Created:  Dec 2025, M. Clarke

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------
# RCAIDE imports
import RCAIDE

# PyQT imports
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QTabWidget

# RCAIDE GUI Imports
from tabs.geometry.widgets.powertrain.distributors import FuelLineWidget
from tabs.geometry.widgets.powertrain.sources import EnergySourceSelectorWidget

from tabs.geometry.frames.powertrain.sources import EnergySourceFrame
from tabs.geometry.frames.powertrain.distributors import DistributorFrame
from tabs.geometry.frames.powertrain.converters import ConverterFrame
from tabs.geometry.frames.powertrain.propulsors import PropulsorFrame
from tabs.geometry.widgets.powertrain.powertrain_connector_widget import PowertrainConnectorWidget
from widgets import DataEntryWidget


# ----------------------------------------------------------------------------------------------------------------------
#  Powertrain Widget
# ---------------------------------------------------------------------------------------------------------------------
class PowertrainWidget(QWidget):
    def __init__(self):
        super(PowertrainWidget, self).__init__()

        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        self.fuellines_layout = QVBoxLayout()  # Define main_layout here
        self.fuellines_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        # header_layout = QHBoxLayout()

        layout = self.create_scroll_layout()

        # add_section_button = QPushButton("Add Fuel Line Section", self)
        # add_section_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        # add_section_button.setMaximumWidth(200)
        # add_section_button.clicked.connect(self.add_fuelline_section)
        # header_layout.addWidget(add_section_button)

        # layout.addLayout(header_layout)

        name_layout = QHBoxLayout()

        layout.addLayout(name_layout)

        # Add line above buttons
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create Propulsors tab
        self.distributor_frame = DistributorFrame()
        self.tab_widget.addTab(self.distributor_frame, "Distributors")

        self.energy_source_frame = EnergySourceFrame()
        self.tab_widget.addTab(
            self.energy_source_frame, "Energy Sources")

        self.propulsor_frame = PropulsorFrame()
        self.tab_widget.addTab(self.propulsor_frame, "Propulsors")

        self.converter_frame = ConverterFrame()
        self.tab_widget.addTab(self.converter_frame, "Converters")

        layout.addWidget(line_bar)
        layout.addLayout(self.fuellines_layout)

        update_selector_button = QPushButton(
            "Update Propulsor-Source Connectivity")
        update_selector_button.setStyleSheet(
            "color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        update_selector_button.clicked.connect(self.update_fuel_selector)
        layout.addWidget(update_selector_button)

        self.fuel_tank_selector = PowertrainConnectorWidget()
        # self.fuel_tank_selector.setTabPosition(QTabWidget.TabPosition.North)
        layout.addWidget(self.fuel_tank_selector)

    def add_fuelline_section(self):
        self.fuellines_layout.addWidget(
            FuelLineWidget(self.fuellines_layout.count(), self.on_delete_button_pressed))

    def update_fuel_selector(self):
        self.fuel_tank_selector.clear()
        data = self.get_data_values(just_data=True)

        self.fuel_tank_selector.update_selector(data)

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

    def create_rcaide_structure(self, distributors, sources, propulsors, converters):
        for distributor in distributors:
            distributor = RCAIDE.Library.Components.Powertrain.Distributors.Fuel_Line()
            distributor.tag = self.section_name_edit.text()

            # propulsor_group = propulsors
            distributor.assigned_propulsors = [[]]
            for propulsor in propulsors:
                distributor.assigned_propulsors[0].append(propulsor.tag)

            for source in sources:
                distributor.fuel_tanks.append(source)  # NEED TO CHANGE

        return distributors, sources, propulsors, converters

    def get_data_values(self, just_data=False):
        """Retrieve the entered data values from both SourceFrame and PropulsorFrame."""
        data = {}

        # Get the name of the fuel line
        # fuel_line_name = self.section_name_edit.text()
        # data["name"] = fuel_line_name

        # Get data values from Distributor tab
        distributor_data = self.distributor_frame.get_data_values()
        data["distributor data"], distributors = distributor_data

        # Get data values from Sources tab
        source_data = self.energy_source_frame.get_data_values()
        data["source data"], sources = source_data

        # Get data values from Propulsors tab
        propulsor_data = self.propulsor_frame.get_data_values()
        data["propulsor data"], propulsors = propulsor_data

        # Get data values from Converters tab
        converter_data = self.converter_frame.get_data_values()
        data["converter data"], converters = converter_data

        if just_data:
            return data

        distributors, sources, propulsors, converters = self.create_rcaide_structure(
            distributors, sources, propulsors, converters)
        return data, distributors, sources, propulsors, converters

    def load_data_values(self, data, index=0):
        distributor_data = data["distributor data"]
        self.distributor_frame.load_data(distributor_data)

        source_data = data["fuel tank data"]
        self.energy_source_frame.load_data(source_data)

        propulsor_data = data["propulsor data"]
        self.propulsor_frame.load_data(propulsor_data)

        converter_data = data["converter data"]
        self.converter_frame.load_data(converter_data)

    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        # Set the main layout inside the scroll content
        layout = QVBoxLayout(scroll_content)

        # Set the main layout of the widget
        self.setLayout(layout)
        return layout
