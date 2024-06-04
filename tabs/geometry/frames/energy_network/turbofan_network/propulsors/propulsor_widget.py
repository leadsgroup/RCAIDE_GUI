from venv import create
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame

from tabs.geometry.frames.energy_network.energy_network_widget import EnergyNetworkWidget
from utilities import Units
from widgets.data_entry_widget import DataEntryWidget

import RCAIDE
from RCAIDE.Library.Methods.Energy.Propulsors.Turbofan_Propulsor import design_turbofan


class PropulsorWidget(QWidget, EnergyNetworkWidget):
    def __init__(self, index, on_delete, data_values=None):
        """Create a frame for entering landing gear data."""
        super(PropulsorWidget, self).__init__()

        self.data_values = {}
        self.index = index
        self.on_delete = on_delete

        main_section_layout = QVBoxLayout()

        # TODO: Change to duplicate turbofan
        # TODO: Make sure 2 turbofans aren't at the same origin

        data_units_labels = [
            ("Turbofan", Units.Heading),
            ("Origin", Units.Position),
            ("Engine Length", Units.Length),
            ("Bypass Ratio", Units.Unitless),
            ("Design Altitude", Units.Length),
            ("Design Mach Number", Units.Unitless),
            ("Design Thrust", Units.Force),
            ("Fan", Units.Heading),
            ("Fan Polytropic Efficiency", Units.Unitless),
            ("Fan Pressure Ratio", Units.Unitless),
            ("Inlet Nozzle", Units.Heading),
            ("IN Polytropic Efficiency", Units.Unitless),
            ("IN Pressure Ratio", Units.Unitless),
            ("Low Pressure Compressor", Units.Heading),
            ("LPC Polytropic Efficiency", Units.Unitless),
            ("LPC Pressure Ratio", Units.Unitless),
            ("High Pressure Compressor", Units.Heading),
            ("HPC Polytropic Efficiency", Units.Unitless),
            ("HPC Pressure Ratio", Units.Unitless),
            ("Low Pressure Turbine", Units.Heading),
            ("LPT Mechanical Efficiency", Units.Unitless),
            ("LPT Polytropic Efficiency", Units.Unitless),
            ("High Pressure Turbine", Units.Heading),
            ("HPT Mechanical Efficiency", Units.Unitless),
            ("HPT Polytropic Efficiency", Units.Unitless),
            ("Combustor", Units.Heading),
            ("Combustor Efficiency", Units.Unitless),
            ("Combustor Pressure Loss Coeff", Units.Unitless),
            ("Combustor Turbine Inlet Temp", Units.Temperature),
            ("Combustor Pressure Ratio", Units.Unitless),
            ("Core Nozzle", Units.Heading),
            ("CN Polytropic Efficiency", Units.Unitless),
            ("CN Pressure Ratio", Units.Unitless),
            ("Fan Nozzle", Units.Heading),
            ("FN Polytropic Efficiency", Units.Unitless),
            ("FN Pressure Ratio", Units.Unitless),
        ]

        self.name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        self.name_layout.addWidget(QLabel("Turbofan Name: "))
        self.name_layout.addWidget(self.section_name_edit)
        main_section_layout.addLayout(self.name_layout)

        self.data_entry_widget = DataEntryWidget(data_units_labels)
        main_section_layout.addWidget(self.data_entry_widget)

        # Adding delete button
        delete_button = QPushButton("Delete Propulsor", self)
        delete_button.clicked.connect(self.delete_button_pressed)

        main_section_layout.addWidget(delete_button)

        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        main_section_layout.addWidget(line_bar)

        self.setLayout(main_section_layout)

        if data_values:
            self.load_data_values(data_values)

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)

    def create_rcaide_structure(self, data):
        turbofan = RCAIDE.Library.Components.Propulsors.Turbofan()
        turbofan.tag = data["propulsor name"][0]
        turbofan.origin = data["Origin"][0]
        turbofan.engine_length = data["Engine Length"][0]
        turbofan.bypass_ratio = data["Bypass Ratio"][0]
        turbofan.design_altitude = data["Design Altitude"][0]
        turbofan.design_mach_number = data["Design Mach Number"][0]
        turbofan.design_thrust = data["Design Thrust"][0]

        fan = RCAIDE.Library.Components.Propulsors.Converters.Fan()
        fan.tag = "fan"
        fan.polytropic_efficiency = data["Fan Polytropic Efficiency"][0]
        fan.pressure_ratio = data["Fan Pressure Ratio"][0]
        turbofan.fan = fan

        turbofan.working_fluid = RCAIDE.Library.Attributes.Gases.Air()
        ram = RCAIDE.Library.Components.Propulsors.Converters.Ram()
        ram.tag = "ram"
        turbofan.ram = ram

        inlet_nozzle = RCAIDE.Library.Components.Propulsors.Converters.Compression_Nozzle()
        inlet_nozzle.tag = "inlet nozzle"
        inlet_nozzle.polytropic_efficiency = data["IN Polytropic Efficiency"][0]
        inlet_nozzle.pressure_ratio = data["IN Pressure Ratio"][0]
        turbofan.inlet_nozzle = inlet_nozzle

        low_pressure_compressor = RCAIDE.Library.Components.Propulsors.Converters.Compressor()
        low_pressure_compressor.tag = "lpc"
        low_pressure_compressor.polytropic_efficiency = data["LPC Polytropic Efficiency"][0]
        low_pressure_compressor.pressure_ratio = data["LPC Pressure Ratio"][0]
        turbofan.low_pressure_compressor = low_pressure_compressor

        high_pressure_compressor = RCAIDE.Library.Components.Propulsors.Converters.Compressor()
        high_pressure_compressor.tag = "hpc"
        high_pressure_compressor.polytropic_efficiency = data["HPC Polytropic Efficiency"][0]
        high_pressure_compressor.pressure_ratio = data["HPC Pressure Ratio"][0]
        turbofan.high_pressure_compressor = high_pressure_compressor

        low_pressure_turbine = RCAIDE.Library.Components.Propulsors.Converters.Turbine()
        low_pressure_turbine.tag = "lpt"
        low_pressure_turbine.mechanical_efficiency = data["LPT Mechanical Efficiency"][0]
        low_pressure_turbine.polytropic_efficiency = data["LPT Polytropic Efficiency"][0]
        turbofan.low_pressure_turbine = low_pressure_turbine

        high_pressure_turbine = RCAIDE.Library.Components.Propulsors.Converters.Turbine()
        high_pressure_turbine.tag = "hpt"
        high_pressure_turbine.mechanical_efficiency = data["HPT Mechanical Efficiency"][0]
        high_pressure_turbine.polytropic_efficiency = data["HPT Polytropic Efficiency"][0]
        turbofan.high_pressure_turbine = high_pressure_turbine

        combustor = RCAIDE.Library.Components.Propulsors.Converters.Combustor()
        combustor.tag = "comb"
        combustor.efficiency = data["Combustor Efficiency"][0]
        combustor.alphac = data["Combustor Pressure Loss Coeff"][0]
        combustor.turbine_inlet_temperature = data["Combustor Turbine Inlet Temp"][0]
        combustor.pressure_ratio = data["Combustor Pressure Ratio"][0]
        combustor.fuel_data = RCAIDE.Library.Attributes.Propellants.Jet_A()
        turbofan.combustor = combustor

        core_nozzle = RCAIDE.Library.Components.Propulsors.Converters.Expansion_Nozzle()
        core_nozzle.tag = "core nozzle"
        core_nozzle.polytropic_efficiency = data["CN Polytropic Efficiency"][0]
        core_nozzle.pressure_ratio = data["CN Pressure Ratio"][0]
        turbofan.core_nozzle = core_nozzle

        fan_nozzle = RCAIDE.Library.Components.Propulsors.Converters.Expansion_Nozzle()
        fan_nozzle.tag = "fan nozzle"
        fan_nozzle.polytropic_efficiency = data["FN Polytropic Efficiency"][0]
        fan_nozzle.pressure_ratio = data["FN Pressure Ratio"][0]
        turbofan.fan_nozzle = fan_nozzle

        design_turbofan(turbofan)

        return turbofan

    def load_data_values(self, data):
        self.data_entry_widget.load_data(data)
        self.section_name_edit.setText(data["propulsor name"])

    def get_data_values(self):
        title = self.section_name_edit.text()
        data = self.data_entry_widget.get_values()
        data["propulsor name"] = title
        return data, self.create_rcaide_structure(self.data_entry_widget.get_values_si())
