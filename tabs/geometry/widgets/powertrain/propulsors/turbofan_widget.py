from lib2to3.pytree import convert # CHECK 
import RCAIDE
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QSpacerItem, QSizePolicy
from tabs.geometry.widgets.powertrain.nacelles.nacelle_section_widget import NacelleSectionWidget
from utilities import Units, convert_name, clear_layout, set_data
from widgets import DataEntryWidget
import values


class TurbofanWidget(QWidget):
    def __init__(self, index, on_delete, data_values=None):
        super(TurbofanWidget, self).__init__()

        self.data_values = {}
        self.index = index
        self.on_delete = on_delete

        main_section_layout = QVBoxLayout()

        data_units_labels = [
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
            ("Inlet Nozzle Polytropic Efficiency", Units.Unitless),
            ("Inlet Nozzle Pressure Ratio", Units.Unitless),
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
            ("Core Nozzle Polytropic Efficiency", Units.Unitless),
            ("Core Nozzle Pressure Ratio", Units.Unitless),
            ("Fan Nozzle", Units.Heading),
            ("Fan Nozzle Polytropic Efficiency", Units.Unitless),
            ("Fan Nozzle Pressure Ratio", Units.Unitless),
        ]

        self.name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        self.name_layout.addWidget(QLabel("Turbofan Name: "))
        self.name_layout.addWidget(self.section_name_edit)
        main_section_layout.addLayout(self.name_layout)

        self.data_entry_widget = DataEntryWidget(data_units_labels)
        main_section_layout.addWidget(self.data_entry_widget)

        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        main_section_layout.addWidget(line_bar)

        main_section_layout.addWidget(QLabel("<b>Nacelle Configuration</b>"))

        nacelle_units_labels = [
            ("Nacelle Length", Units.Length, "length"),
            ("Inlet Diameter", Units.Length, "inlet_diameter"),
            ("Diameter", Units.Length, "diameter"),
            ("Nacelle Origin", Units.Position, "origin"),
            ("Wetted Area", Units.Area, "areas.wetted"),
            ("Flow Through", Units.Boolean, "flow_through"),
        ]
        
        self.nacelle_general_widget = DataEntryWidget(nacelle_units_labels)
        main_section_layout.addWidget(self.nacelle_general_widget)

        main_section_layout.addWidget(QLabel("<b>Nacelle Sections</b>"))
        
        self.nacelle_sections_layout = QVBoxLayout()
        main_section_layout.addLayout(self.nacelle_sections_layout)

        add_section_btn = QPushButton("Add Nacelle Section", self)
        add_section_btn.clicked.connect(self.add_nacelle_section)
        add_section_btn.setStyleSheet("color:#dbe7ff; font-weight:500;")
        main_section_layout.addWidget(add_section_btn)

        line_bar2 = QFrame()
        line_bar2.setFrameShape(QFrame.Shape.HLine)
        line_bar2.setFrameShadow(QFrame.Shadow.Sunken)
        main_section_layout.addWidget(line_bar2)

        delete_button = QPushButton("Delete Turbofan", self)
        delete_button.clicked.connect(self.delete_button_pressed) 
        main_section_layout.addWidget(delete_button)

        self.setLayout(main_section_layout)

        if data_values:
            self.load_data_values(data_values)

    def add_nacelle_section(self):
        self.nacelle_sections_layout.addWidget(NacelleSectionWidget(
            self.nacelle_sections_layout.count(), self.delete_nacelle_section))

    def delete_nacelle_section(self, index):
        item = self.nacelle_sections_layout.itemAt(index)
        if item is None: return

        widget = item.widget()
        if widget is None or not isinstance(widget, NacelleSectionWidget): return

        widget.deleteLater()
        self.nacelle_sections_layout.removeWidget(widget)
        self.nacelle_sections_layout.update()

        for i in range(index, self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None: continue
            widget = item.widget()
            if widget is not None and isinstance(widget, NacelleSectionWidget):
                widget.index = i

    def delete_button_pressed(self): 
        if self.on_delete is None:
            print("on_delete is None")
            return
        self.on_delete(self.index)

    def get_data_values(self):
        title = self.section_name_edit.text()
        
        data = self.data_entry_widget.get_values()
        data["Propulsor Tag"] = title
        
        nacelle_data = self.nacelle_general_widget.get_values()
        nacelle_data["sections"] = []
        
        section_objects = [] 
        
        for i in range(self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None: continue
            
            widget = item.widget()
            if widget is not None and isinstance(widget, NacelleSectionWidget):
                s_data, s_object = widget.get_data_values()
                nacelle_data["sections"].append(s_data)
                section_objects.append(s_object)

        data["nacelle_data"] = nacelle_data
        values.propulsor_names[0].append(convert_name(title))

        data_si = self.data_entry_widget.get_values_si()
        data_si["Propulsor Tag"] = title
        
        nacelle_si = self.nacelle_general_widget.get_values_si()
        nacelle_si["section_objects"] = section_objects
        
        data_si["nacelle_si"] = nacelle_si

        return data, self.create_rcaide_structure(data_si)

    def create_rcaide_structure(self, data):
        turbofan = RCAIDE.Library.Components.Powertrain.Propulsors.Turbofan()
        turbofan.tag = data["Propulsor Tag"]
        turbofan.origin = data["Origin"][0]
        turbofan.engine_length = data["Engine Length"][0]
        turbofan.bypass_ratio = data["Bypass Ratio"][0]
        turbofan.design_altitude = data["Design Altitude"][0]
        turbofan.design_mach_number = data["Design Mach Number"][0]
        turbofan.design_thrust = data["Design Thrust"][0]
            
        fan = RCAIDE.Library.Components.Powertrain.Converters.Fan()
        fan.tag = "fan"
        fan.polytropic_efficiency = data["Fan Polytropic Efficiency"][0]
        fan.pressure_ratio = data["Fan Pressure Ratio"][0]
        turbofan.fan = fan
            
        turbofan.working_fluid = RCAIDE.Library.Attributes.Gases.Air()
        ram = RCAIDE.Library.Components.Powertrain.Converters.Ram()
        ram.tag = "ram"
        turbofan.ram = ram
            
        inlet_nozzle = RCAIDE.Library.Components.Powertrain.Converters.Compression_Nozzle()
        inlet_nozzle.tag = "inlet nozzle"
        inlet_nozzle.polytropic_efficiency = data["Inlet Nozzle Polytropic Efficiency"][0]
        inlet_nozzle.pressure_ratio = data["Inlet Nozzle Pressure Ratio"][0]
        turbofan.inlet_nozzle = inlet_nozzle

        low_pressure_compressor = RCAIDE.Library.Components.Powertrain.Converters.Compressor()
        low_pressure_compressor.tag = "lpc"
        low_pressure_compressor.polytropic_efficiency = data["LPC Polytropic Efficiency"][0]
        low_pressure_compressor.pressure_ratio = data["LPC Pressure Ratio"][0]
        turbofan.low_pressure_compressor = low_pressure_compressor

        high_pressure_compressor = RCAIDE.Library.Components.Powertrain.Converters.Compressor()
        high_pressure_compressor.tag = "hpc"
        high_pressure_compressor.polytropic_efficiency = data["HPC Polytropic Efficiency"][0]
        high_pressure_compressor.pressure_ratio = data["HPC Pressure Ratio"][0]
        turbofan.high_pressure_compressor = high_pressure_compressor

        low_pressure_turbine = RCAIDE.Library.Components.Powertrain.Converters.Turbine()
        low_pressure_turbine.tag = "lpt"
        low_pressure_turbine.mechanical_efficiency = data["LPT Mechanical Efficiency"][0]
        low_pressure_turbine.polytropic_efficiency = data["LPT Polytropic Efficiency"][0]
        turbofan.low_pressure_turbine = low_pressure_turbine

        high_pressure_turbine = RCAIDE.Library.Components.Powertrain.Converters.Turbine()
        high_pressure_turbine.tag = "hpt"
        high_pressure_turbine.mechanical_efficiency = data["HPT Mechanical Efficiency"][0]
        high_pressure_turbine.polytropic_efficiency = data["HPT Polytropic Efficiency"][0]
        turbofan.high_pressure_turbine = high_pressure_turbine

        combustor = RCAIDE.Library.Components.Powertrain.Converters.Combustor()
        combustor.tag = "comb"
        combustor.efficiency = data["Combustor Efficiency"][0]
        combustor.alphac = data["Combustor Pressure Loss Coeff"][0]
        combustor.turbine_inlet_temperature = data["Combustor Turbine Inlet Temp"][0]
        combustor.pressure_ratio = data["Combustor Pressure Ratio"][0]
        combustor.fuel_data = RCAIDE.Library.Attributes.Propellants.Jet_A1()
        turbofan.combustor = combustor

        core_nozzle = RCAIDE.Library.Components.Powertrain.Converters.Expansion_Nozzle()
        core_nozzle.tag = "core nozzle"
        core_nozzle.polytropic_efficiency = data["Core Nozzle Polytropic Efficiency"][0]
        core_nozzle.pressure_ratio = data["Core Nozzle Pressure Ratio"][0]
        turbofan.core_nozzle = core_nozzle

        fan_nozzle = RCAIDE.Library.Components.Powertrain.Converters.Expansion_Nozzle()
        fan_nozzle.tag = "fan nozzle"
        fan_nozzle.polytropic_efficiency = data["Fan Nozzle Polytropic Efficiency"][0]
        fan_nozzle.pressure_ratio = data["Fan Nozzle Pressure Ratio"][0]
        turbofan.fan_nozzle = fan_nozzle

        if "nacelle_si" in data:
            n_data = data["nacelle_si"]
        
            nacelle = RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle()
            nacelle.tag = str(data["Propulsor Tag"]) + "_nacelle"
        
            nacelle.length          = n_data["Nacelle Length"][0]
            nacelle.inlet_diameter  = n_data["Inlet Diameter"][0]
            nacelle.diameter        = n_data["Diameter"][0]
            nacelle.areas.wetted    = n_data["Wetted Area"][0]
            nacelle.flow_through    = n_data["Flow Through"][0]
            nacelle.origin = n_data["Nacelle Origin"][0]
            
            nacelle_airfoil = RCAIDE.Library.Components.Airfoils.NACA_4_Series_Airfoil()
            nacelle_airfoil.NACA_4_Series_code = '2410'
            nacelle.append_airfoil(nacelle_airfoil) 

            if "section_objects" in n_data:
                for segment in n_data["section_objects"]:
                    nacelle.append_segment(segment)
            
            turbofan.nacelle = nacelle

        return turbofan

    def load_data_values(self, data):
        self.data_entry_widget.load_data(data)
        self.section_name_edit.setText(data.get("Propulsor Tag", ""))
        
        if "nacelle_data" in data:
            n_data = data["nacelle_data"]
            self.nacelle_general_widget.load_data(n_data)
            
            clear_layout(self.nacelle_sections_layout)
            
            if "sections" in n_data:
                for section_data in n_data["sections"]:
                    self.add_nacelle_section()
                    last_widget = self.nacelle_sections_layout.itemAt(
                        self.nacelle_sections_layout.count() - 1).widget()
                    last_widget.load_data_values(section_data)