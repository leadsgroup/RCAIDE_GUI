# RCAIDE_GUI/tabs/geometry/widgets/powertrain/propulsors/turbofan_widget.py

# Created: Dec 2025, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QSpacerItem, QSizePolicy, QComboBox, QFileDialog
from tabs.geometry.widgets.powertrain.nacelles.nacelle_section_widget import NacelleSectionWidget
from RCAIDE.Library.Methods.Powertrain.Propulsors.Turbofan    import design_turbofan  
from utilities import Units, convert_name, clear_layout, set_data, set_if_changed, get_path_value
from common_widgets import DataEntryWidget
from PyQt6.QtCore import Qt
import rcaide_io


# Turbofan form fields as (display label, GUI unit type, RCAIDE attribute path)
TURBOFAN_FIELDS = [
    ("Origin",                                  Units.Position,    "origin"),
    ("Engine Length",                           Units.Length,      "length"),
    ("Diameter",                                Units.Length,      "diameter"),
    ("Bypass Ratio",                            Units.Unitless,    "bypass_ratio"),
    ("Design Point",                            Units.Heading,     ""),
    ("Design Altitude",                         Units.Length,      "design_altitude"),
    ("Design Mach Number",                      Units.Unitless,    "design_mach_number"),
    ("Design ISA Deviation",                    Units.Temperature, "design_isa_deviation"),
    ("Design Thrust",                           Units.Force,       "design_thrust"),
    ("Rated Takeoff Thrust",                    Units.Force,       "rated_takeoff_thrust"),
    ("Takeoff Combustor Exit Temperature Ratio", Units.Unitless,   "takeoff_combustor_exit_temperature_ratio"),
    ("Fan",                                     Units.Heading,     ""),
    ("Fan Polytropic Efficiency",               Units.Unitless,    "fan.polytropic_efficiency"),
    ("Fan Pressure Ratio",                      Units.Unitless,    "fan.pressure_ratio"),
    ("Fan Rated Angular Velocity (rad/s)",      Units.Unitless,    "fan.rated_angular_velocity"),
    ("Inlet Nozzle",                            Units.Heading,     ""),
    ("Inlet Nozzle Polytropic Efficiency",      Units.Unitless,    "inlet_nozzle.polytropic_efficiency"),
    ("Inlet Nozzle Pressure Ratio",             Units.Unitless,    "inlet_nozzle.pressure_ratio"),
    ("Inlet Nozzle Compressibility Effects",    Units.Boolean,     "inlet_nozzle.compressibility_effects"),
    ("Low Pressure Compressor",                 Units.Heading,     ""),
    ("LPC Polytropic Efficiency",               Units.Unitless,    "low_pressure_compressor.polytropic_efficiency"),
    ("LPC Pressure Ratio",                      Units.Unitless,    "low_pressure_compressor.pressure_ratio"),
    ("High Pressure Compressor",                Units.Heading,     ""),
    ("HPC Polytropic Efficiency",               Units.Unitless,    "high_pressure_compressor.polytropic_efficiency"),
    ("HPC Pressure Ratio",                      Units.Unitless,    "high_pressure_compressor.pressure_ratio"),
    ("Low Pressure Turbine",                    Units.Heading,     ""),
    ("LPT Mechanical Efficiency",               Units.Unitless,    "low_pressure_turbine.mechanical_efficiency"),
    ("LPT Polytropic Efficiency",               Units.Unitless,    "low_pressure_turbine.polytropic_efficiency"),
    ("High Pressure Turbine",                   Units.Heading,     ""),
    ("HPT Mechanical Efficiency",               Units.Unitless,    "high_pressure_turbine.mechanical_efficiency"),
    ("HPT Polytropic Efficiency",               Units.Unitless,    "high_pressure_turbine.polytropic_efficiency"),
    ("Combustor",                               Units.Heading,     ""),
    ("Combustor Efficiency",                    Units.Unitless,    "combustor.efficiency"),
    ("Combustor Pressure Loss Coeff",           Units.Unitless,    "combustor.alphac"),
    ("Combustor Turbine Inlet Temp",            Units.Temperature, "combustor.turbine_inlet_temperature"),
    ("Combustor Pressure Ratio",                Units.Unitless,    "combustor.pressure_ratio"),
    ("Core Nozzle",                             Units.Heading,     ""),
    ("Core Nozzle Polytropic Efficiency",       Units.Unitless,    "core_nozzle.polytropic_efficiency"),
    ("Core Nozzle Pressure Ratio",              Units.Unitless,    "core_nozzle.pressure_ratio"),
    ("Fan Nozzle",                              Units.Heading,     ""),
    ("Fan Nozzle Polytropic Efficiency",        Units.Unitless,    "fan_nozzle.polytropic_efficiency"),
    ("Fan Nozzle Pressure Ratio",               Units.Unitless,    "fan_nozzle.pressure_ratio"),
]

# Sub-components a new turbofan needs before its fields can be set
TURBOFAN_SUBCOMPONENTS = {
    "fan":                      RCAIDE.Library.Components.Powertrain.Converters.Fan,
    "ram":                      RCAIDE.Library.Components.Powertrain.Converters.Ram,
    "inlet_nozzle":             RCAIDE.Library.Components.Powertrain.Converters.Compression_Nozzle,
    "low_pressure_compressor":  RCAIDE.Library.Components.Powertrain.Converters.Compressor,
    "high_pressure_compressor": RCAIDE.Library.Components.Powertrain.Converters.Compressor,
    "low_pressure_turbine":     RCAIDE.Library.Components.Powertrain.Converters.Turbine,
    "high_pressure_turbine":    RCAIDE.Library.Components.Powertrain.Converters.Turbine,
    "combustor":                RCAIDE.Library.Components.Powertrain.Converters.Combustor,
    "core_nozzle":              RCAIDE.Library.Components.Powertrain.Converters.Expansion_Nozzle,
    "fan_nozzle":               RCAIDE.Library.Components.Powertrain.Converters.Expansion_Nozzle,
}


class TurbofanWidget(QWidget):
    def __init__(self, index, on_delete, data_values=None):
        super(TurbofanWidget, self).__init__()

        self.data_values = {}
        self.index = index
        self.on_delete = on_delete

        self.nacelle_active = False

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.loaded_component = None

        self.name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        self.name_layout.addWidget(QLabel("Turbofan Name: "))
        self.name_layout.addWidget(self.section_name_edit)
        self.main_layout.addLayout(self.name_layout)

        self.data_entry_widget = DataEntryWidget([(label, units) for label, units, _path in TURBOFAN_FIELDS])
        self.main_layout.addWidget(self.data_entry_widget)

        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line_bar)

        self.add_nacelle_btn = QPushButton("Add Nacelle", self)
        self.add_nacelle_btn.clicked.connect(self.enable_nacelle_ui)
        self.add_nacelle_btn.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        self.main_layout.addWidget(self.add_nacelle_btn)

        self.nacelle_container = QWidget()
        self.nacelle_layout = QVBoxLayout(self.nacelle_container)
        # self.nacelle_layout.setContentsMargins(0, 10, 0, 0)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Nacelle Configuration</b>"))
        header_layout.addStretch()
        
        self.remove_nacelle_btn = QPushButton("Remove Nacelle", self)
        self.remove_nacelle_btn.clicked.connect(self.disable_nacelle_ui)
        self.remove_nacelle_btn.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        self.remove_nacelle_btn.setFixedWidth(150)
        header_layout.addWidget(self.remove_nacelle_btn)
        
        self.nacelle_layout.addLayout(header_layout)

        nacelle_type_layout = QHBoxLayout()
        nacelle_type_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        nacelle_type_layout.addWidget(QLabel("Nacelle Type: "))
        self.nacelle_combo = QComboBox()
        self.nacelle_combo.addItems(["Select Nacelle Type", "Generic Nacelle", "Body of Revolution", "Stack Nacelle"])
        self.nacelle_combo.setFixedWidth(600)
        nacelle_type_layout.addWidget(self.nacelle_combo, alignment=Qt.AlignmentFlag.AlignCenter)
        nacelle_type_layout.addItem(QSpacerItem(200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.nacelle_layout.addLayout(nacelle_type_layout)

        nacelle_units_labels = [
            ("Nacelle Length", Units.Length, "length"),
            ("Inlet Diameter", Units.Length, "inlet_diameter"),
            ("Diameter", Units.Length, "diameter"),
            ("Nacelle Origin", Units.Position, "origin"),
            ("Wetted Area", Units.Area, "areas.wetted"),
            ("Flow Through", Units.Boolean, "flow_through"),
        ]
        self.nacelle_general_widget = DataEntryWidget(nacelle_units_labels)
        self.nacelle_layout.addWidget(self.nacelle_general_widget)

        self.nacelle_layout.addWidget(QLabel("<b>Nacelle Airfoil</b>"))
        airfoil_layout = QHBoxLayout()
        airfoil_left_col = QVBoxLayout()
        type_layout = QHBoxLayout()
        self.airfoil_type_label = QLabel("Airfoil Type:")
        self.airfoil_type_combo = QComboBox()
        self.airfoil_type_combo.addItems(["None (Auto)", "NACA 4-Series", "Coordinate File"])
        self.airfoil_type_combo.currentTextChanged.connect(self._update_airfoil_ui_state)
        type_layout.addWidget(self.airfoil_type_label)
        type_layout.addWidget(self.airfoil_type_combo)
        airfoil_left_col.addLayout(type_layout)

        self.naca_layout = QHBoxLayout()
        self.naca_code_label = QLabel("NACA Code:")
        self.naca_code_input = QLineEdit()
        self.naca_code_input.setPlaceholderText("e.g. 0012")
        self.naca_layout.addWidget(self.naca_code_label)
        self.naca_layout.addWidget(self.naca_code_input)
        airfoil_left_col.addLayout(self.naca_layout)
        
        # Right Column (File Path)
        airfoil_right_col = QVBoxLayout()
        self.file_layout = QHBoxLayout()
        self.file_path_label = QLabel("File Path:")
        self.file_path_input = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_for_file)
        self.file_layout.addWidget(self.file_path_label)
        self.file_layout.addWidget(self.file_path_input)
        self.file_layout.addWidget(self.browse_button)
        airfoil_right_col.addLayout(self.file_layout)

        airfoil_layout.addLayout(airfoil_left_col)
        airfoil_layout.addLayout(airfoil_right_col)
        self.nacelle_layout.addLayout(airfoil_layout)
        
        # Initialize Airfoil UI State
        self._update_airfoil_ui_state()

        self.nacelle_layout.addWidget(QLabel("<b>Nacelle Sections</b>"))
        self.nacelle_sections_layout = QVBoxLayout()
        self.nacelle_layout.addLayout(self.nacelle_sections_layout)

        add_section_btn = QPushButton("Add Nacelle Section", self)
        add_section_btn.clicked.connect(self.add_nacelle_section)
        add_section_btn.setStyleSheet("color:#dbe7ff; font-weight:500;")
        self.nacelle_layout.addWidget(add_section_btn)

        self.main_layout.addWidget(self.nacelle_container)

        line_bar2 = QFrame()
        line_bar2.setFrameShape(QFrame.Shape.HLine)
        line_bar2.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line_bar2)

        delete_tf_button = QPushButton("Delete Turbofan", self)
        delete_tf_button.clicked.connect(self.delete_button_pressed) 
        self.main_layout.addWidget(delete_tf_button)
        self.disable_nacelle_ui()

        self.setLayout(self.main_layout)

        # Saved aircraft data fills the form; a new turbofan starts from RCAIDE defaults
        self.load_data_values(data_values or {})

    def _browse_for_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Airfoil File", "", "Data Files (*.dat);;All Files (*)")
        if file_path:
            self.file_path_input.setText(file_path)

    def _update_airfoil_ui_state(self):
        selected_type = self.airfoil_type_combo.currentText()
        
        if selected_type == "NACA 4-Series":
            self.naca_code_label.setVisible(True)
            self.naca_code_input.setVisible(True)
            self.file_path_label.setVisible(False)
            self.file_path_input.setVisible(False)
            self.browse_button.setVisible(False)
        elif selected_type == "Coordinate File":
            self.naca_code_label.setVisible(False)
            self.naca_code_input.setVisible(False)
            self.file_path_label.setVisible(True)
            self.file_path_input.setVisible(True)
            self.browse_button.setVisible(True)
        else:
            self.naca_code_label.setVisible(False)
            self.naca_code_input.setVisible(False)
            self.file_path_label.setVisible(False)
            self.file_path_input.setVisible(False)
            self.browse_button.setVisible(False)
    
    def enable_nacelle_ui(self):
        self.nacelle_active = True
        self.nacelle_container.setVisible(True)
        self.add_nacelle_btn.setVisible(False)
        if self.nacelle_combo.currentIndex() == 0:
            self.nacelle_combo.setCurrentText("Body of Revolution")

    def disable_nacelle_ui(self):
        self.nacelle_active = False
        self.nacelle_container.setVisible(False)
        self.add_nacelle_btn.setVisible(True)
        self.nacelle_combo.setCurrentIndex(0)
        clear_layout(self.nacelle_sections_layout)

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
            return
        self.on_delete(self.index)

    def get_data_values(self):
        title = self.section_name_edit.text()
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data["Propulsor Tag"] = title
        data["Propulsor Type"] = "Turbofan"
        data_si["Propulsor Tag"] = title
        data_si["Propulsor Type"] = "Turbofan"
        if self.loaded_component is not None:
            data["rcaide_component"] = self.loaded_component

        if self.nacelle_active:
            nacelle_data = self.nacelle_general_widget.get_values()
            nacelle_data["Nacelle Type"] = self.nacelle_combo.currentText()
            af_type = self.airfoil_type_combo.currentText()
            nacelle_data["Airfoil Type"] = af_type
            if af_type == "NACA 4-Series":
                nacelle_data["Airfoil Code"] = self.naca_code_input.text()
            elif af_type == "Coordinate File":
                nacelle_data["Airfoil Path"] = self.file_path_input.text()
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
            rcaide_io.propulsor_names[0].append(convert_name(title))

            data_si = self.data_entry_widget.get_values_si()
            data_si["Propulsor Tag"] = title
            data_si["Propulsor Type"] = "Turbofan"
            
            nacelle_si = self.nacelle_general_widget.get_values_si()
            nacelle_si["Nacelle Type"] = self.nacelle_combo.currentText()
            nacelle_si["Airfoil Type"] = af_type
            nacelle_si["Airfoil Code"] = self.naca_code_input.text()
            nacelle_si["Airfoil Path"] = self.file_path_input.text()
            nacelle_si["section_objects"] = section_objects
            
            data_si["nacelle_si"] = nacelle_si
        
        rcaide_io.propulsor_names[0].append(convert_name(title))



        return data, self.create_rcaide_structure(data_si)

    def base_turbofan(self):
        """Return the loaded RCAIDE turbofan, or a new one with RCAIDE defaults and all sub-components."""
        if self.loaded_component is not None:
            return rcaide_io.component_from_dict(self.loaded_component)
        turbofan = RCAIDE.Library.Components.Powertrain.Propulsors.Turbofan()
        for attr_name, component_class in TURBOFAN_SUBCOMPONENTS.items():
            component = component_class()
            component.tag = attr_name
            turbofan[attr_name] = component
        turbofan.combustor.fuel_data = RCAIDE.Library.Attributes.Propellants.Jet_A1()
        return turbofan

    def create_rcaide_structure(self, data):
        # Start from the loaded turbofan so settings the form does not show are kept
        turbofan = self.base_turbofan()
        turbofan.tag = data["Propulsor Tag"]
        for label, units, path in TURBOFAN_FIELDS:
            if units == Units.Heading or label not in data:
                continue
            set_if_changed(turbofan, path, data[label][0])

        # The nacelle comes from the nacelle form below; no form means no nacelle
        loaded_nacelle   = turbofan.nacelle
        turbofan.nacelle = None
        n_data = data.get("nacelle_si", {})
        n_type = n_data.get("Nacelle Type", "Select Nacelle Type")
        if n_type != "Select Nacelle Type":
            if (n_type == "Generic Nacelle"):
                nacelle = RCAIDE.Library.Components.Nacelles.Nacelle()
            elif (n_type == "Stack Nacelle"):
                nacelle = RCAIDE.Library.Components.Nacelles.Stack_Nacelle()
            elif (n_type == "Body of Revolution"):
                nacelle = RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle()
            else:
                nacelle = RCAIDE.Library.Components.Nacelles.Nacelle() #set as default
            nacelle.tag = str(data["Propulsor Tag"]) + "_nacelle"

            # Keep the loaded nacelle (tag, airfoil, other settings) when its type is unchanged
            if type(loaded_nacelle) is type(nacelle):
                nacelle = loaded_nacelle
        
            nacelle.length          = n_data["Nacelle Length"][0]
            nacelle.inlet_diameter  = n_data["Inlet Diameter"][0]
            nacelle.diameter        = n_data["Diameter"][0]
            nacelle.areas.wetted    = n_data["Wetted Area"][0]
            nacelle.flow_through    = n_data["Flow Through"][0]
            nacelle.origin = n_data["Nacelle Origin"][0]

            af_type = n_data.get("Airfoil Type", "None (Auto)")
            if af_type == "NACA 4-Series":
                code = n_data.get("Airfoil Code", "0012")
                if not code: code = "0012"
                nacelle_airfoil = RCAIDE.Library.Components.Airfoils.NACA_4_Series_Airfoil()
                nacelle_airfoil.NACA_4_Series_code = code
                nacelle.append_airfoil(nacelle_airfoil)
                        
            elif af_type == "Coordinate File":
                path = n_data.get("Airfoil Path", "")
                if path and os.path.exists(path):
                    nacelle_airfoil = RCAIDE.Library.Components.Airfoils.Airfoil()
                    nacelle_airfoil.coordinate_file = path
                    nacelle.append_airfoil(nacelle_airfoil)
                else:
                    raise FileNotFoundError("Airfoil file not found")
            else:
                pass
            
            if n_type == "Stack Nacelle":
                # Sections come from the section editors
                nacelle.segments = RCAIDE.Framework.Core.Container()
                for seg in n_data.get("section_objects", []):
                    if seg is not None:
                        nacelle.append_segment(seg)

            turbofan.nacelle = nacelle

        # design turbofan
        design_turbofan(turbofan)
        
        return turbofan

    def load_data_values(self, data):
        self.loaded_component = data.get("rcaide_component")
        turbofan = self.base_turbofan()
        form_data = {}
        for label, units, path in TURBOFAN_FIELDS:
            if units == Units.Heading:
                continue
            form_data[label] = data.get(label, [get_path_value(turbofan, path), 0])
        self.data_entry_widget.load_data(form_data)
        self.section_name_edit.setText(data.get("Propulsor Tag", ""))
        
        if "nacelle_data" in data:   
            n_data = data["nacelle_data"]
            self.nacelle_general_widget.load_data(n_data)
            self.enable_nacelle_ui()

            if "Nacelle Type" in n_data:
                self.nacelle_combo.setCurrentText(n_data["Nacelle Type"])
                
            af_type = n_data.get("Airfoil Type", "None (Auto)")
            self.airfoil_type_combo.setCurrentText(af_type)
            self.naca_code_input.setText(n_data.get("Airfoil Code", ""))
            self.file_path_input.setText(n_data.get("Airfoil Path", ""))
            self._update_airfoil_ui_state()

            # if n_data["Nacelle Type"] == "Select Nacelle Type":
            #     self.disable_nacelle_ui()
            # else:
            #     self.enable_nacelle_ui()
            
            clear_layout(self.nacelle_sections_layout)
            
            if "sections" in n_data:
                for section_data in n_data["sections"]:
                    self.add_nacelle_section()
                    last_widget = self.nacelle_sections_layout.itemAt(
                        self.nacelle_sections_layout.count() - 1).widget()
                    last_widget.load_data_values(section_data)
        else:
            self.disable_nacelle_ui()
