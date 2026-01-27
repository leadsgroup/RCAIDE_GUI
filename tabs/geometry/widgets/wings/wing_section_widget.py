# RCAIDE_GUI/tabs/geometry/widgets/wing_section_widget.py
# 
# Created: Oct 2024, Laboratry for Electric Aircraft Design and Sustainabiltiy

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
# RCAIDE imports  
import RCAIDE

# PtQt imports  
from PyQt6.QtWidgets import (QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget, QFrame, QComboBox, QFileDialog)

# gui imports 
from utilities import Units
from widgets import DataEntryWidget
import os
import sys

# ----------------------------------------------------------------------------------------------------------------------
#  WingSectionWidget
# ---------------------------------------------------------------------------------------------------------------------- 
class WingSectionWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None):
        super(WingSectionWidget, self).__init__()

        # self.data_fields = {}
        self.coordinate_filename = ""
        self.index = index
        self.on_delete = on_delete
        self.data_entry_widget: DataEntryWidget | None = None

        self.airfoil_type_combo: QComboBox | None = None
        self.airfoil_code_label: QLabel | None = None
        self.airfoil_code_line_input: QLineEdit | None = None
        self.file_path_label: QLabel | None = None
        self.file_path_line_input: QLineEdit | None = None
        self.browse_button: QPushButton | None = None

        self.name_layout = QHBoxLayout()
        self.init_ui(section_data)

    # noinspection DuplicatedCode
    def init_ui(self, section_data):
        main_layout = QVBoxLayout()
        # add spacing
        spacer_left = QSpacerItem(80, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(300, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_layout.addItem(spacer_left)
        self.name_layout.addWidget(QLabel("Wing Segment Name: "))
        self.name_layout.addWidget(QLineEdit(self))
        self.name_layout.addItem(spacer_right)

        main_layout.addLayout(self.name_layout)

        # List of data labels
        data_units_labels = [
            ("Percent Span Location", Units.Unitless),
            ("Twist", Units.Angle),
            ("Root Chord Percent", Units.Unitless),
            ("Thickness to Chord", Units.Unitless),
            ("Dihedral Outboard", Units.Angle),
            ("Quarter Chord Sweep", Units.Angle),
            ("Has Fuel Tank", Units.Boolean),
            ("Has Aft Fuel Tank", Units.Boolean),
        ]

        self.data_entry_widget = DataEntryWidget(data_units_labels)

        # Delete button
        # delete_button = QPushButton("Delete Wing Segment", self)
        # # delete_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # # delete_button.setFixedWidth(150)
        # delete_button.clicked.connect(self.delete_button_pressed)

        # # Center delete button
        # delete_button_layout = QHBoxLayout()
        # # delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        # delete_button_layout.addWidget(delete_button)
        # # delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        main_layout.addWidget(self.data_entry_widget)
        # main_layout.addLayout(delete_button_layout)

        airfoil_layout = QHBoxLayout() 
        airfoil_left_col = QVBoxLayout()
        airfoil_right_col = QVBoxLayout()

        airfoil_type_layout = QHBoxLayout()
        self.airfoil_type_label = QLabel("Airfoil Type:")
        self.airfoil_type_combo = QComboBox()
        self.airfoil_type_combo.addItems(["None", "NACA 4-Series", "Coordinate File"])
        self.airfoil_type_combo.currentTextChanged.connect(self._update_airfoil_ui_state)
        airfoil_type_layout.addWidget(self.airfoil_type_label)
        airfoil_type_layout.addWidget(self.airfoil_type_combo)
        airfoil_type_layout.addStretch()
        airfoil_left_col.addLayout(airfoil_type_layout)

        self.naca_layout = QHBoxLayout()
        self.naca_code_label = QLabel("NACA Code:")
        self.naca_code_input = QLineEdit()
        self.naca_code_input.setPlaceholderText("ex: 0012")
        self.naca_layout.addWidget(self.naca_code_label)
        self.naca_layout.addWidget(self.naca_code_input)
        self.naca_layout.addStretch()
        airfoil_left_col.addLayout(self.naca_layout)

        self.file_layout = QHBoxLayout()
        self.file_path_label = QLabel("Airfoil File Path:")
        self.file_path_input = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_for_file)
        self.file_layout.addWidget(self.file_path_label)
        self.file_layout.addWidget(self.file_path_input)
        self.file_layout.addWidget(self.browse_button)
        airfoil_right_col.addLayout(self.file_layout)

        airfoil_layout.addLayout(airfoil_left_col, 1)
        airfoil_layout.addLayout(airfoil_right_col, 1)

        main_layout.addLayout(airfoil_layout)

        delete_button = QPushButton("Delete Wing Segment", self)
        delete_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        delete_button.clicked.connect(self.delete_button_pressed)
        delete_button_layout = QHBoxLayout()
        delete_button_layout.addWidget(delete_button)
        main_layout.addLayout(delete_button_layout)

        # Add horizontal bar
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line_bar)

        if section_data:
            self.load_data_values(section_data)

        self.setLayout(main_layout)

        self._update_airfoil_ui_state()


    def create_rcaide_structure(self, data):  
        ospath                                = os.path.abspath(__file__)
        separator                             = os.path.sep    
        segment = RCAIDE.Library.Components.Wings.Segments.Segment()

        segment.tag                   = data["Segment Name"]
        segment.percent_span_location = data["Percent Span Location"][0]
        segment.twist                 = data["Twist"][0] 
        segment.root_chord_percent    = data["Root Chord Percent"][0]
        segment.thickness_to_chord    = data["Thickness to Chord"][0]
        segment.dihedral_outboard     = data["Dihedral Outboard"][0]
        segment.sweeps.quarter_chord  = data["Quarter Chord Sweep"][0]
        
        
        airfoil_type                  = data.get("Airfoil Type", None)
        airfoil_code                  = data.get("Airfoil Code", None)
        airfoil_coordinate_file_path  = data.get("Airfoil Coordinate File Path", None)
        airfoil_points                = data.get("Airfoil Points", 100)
        if airfoil_type == None:
            pass
        elif airfoil_type == "NACA 4-Series":
            airfoil = RCAIDE.Library.Components.Airfoils.NACA_4_Series_Airfoil()
            try: 
                airfoil.NACA_4_Series_code = airfoil_code
            except: 
                airfoil.number_of_points   = airfoil_points                
                airfoil.NACA_4_Series_code = '0012'
            segment.append_airfoil(airfoil)          
        elif airfoil_type == "Coordinate File": 
            airfoil                          = RCAIDE.Library.Components.Airfoils.Airfoil() 
            airfoil.coordinate_file          = 'app_data' + separator + 'aircraft' + separator +  airfoil_coordinate_file_path  
            airfoil.number_of_points         = airfoil_points  
            segment.append_airfoil(airfoil)           

        return segment

    def _browse_for_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Airfoil File", "", "Data Files (*.dat);;All Files (*)")
        if file_path:
            self.file_path_input.setText(file_path)

    def _update_airfoil_ui_state(self):
        selected_type = self.airfoil_type_combo.currentText()
        
        if selected_type == "NACA 4-Series":
            # show left col
            self.naca_code_label.show()
            self.naca_code_input.show()
            
            # hide right col
            self.file_path_label.hide()
            self.file_path_input.hide()
            self.browse_button.hide()
            
        elif selected_type == "Coordinate File":
            # hide left col
            self.naca_code_label.hide()
            self.naca_code_input.hide()
            
            # show right col
            self.file_path_label.show()
            self.file_path_input.show()
            self.browse_button.show()
            
        else: 
            # hide both
            self.naca_code_label.hide()
            self.naca_code_input.hide()
            
            self.file_path_label.hide()
            self.file_path_input.hide()
            self.browse_button.hide()
    
    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data_si["Segment Name"] = self.name_layout.itemAt(2).widget().text()
        airfoil_type = self.airfoil_type_combo.currentText()
        if airfoil_type != "None":
            data["Airfoil Type"] = airfoil_type
            data["Airfoil Code"] = self.naca_code_input.text()
            data["Airfoil Coordinate File Path"] = self.file_path_input.text()
            data_si["Airfoil Type"] = airfoil_type
            data_si["Airfoil Code"] = self.naca_code_input.text()
            data_si["Airfoil Coordinate File Path"] = self.file_path_input.text()
            data_si["Airfoil Points"] = 100 
        else:
            data_si["Airfoil Type"] = None
            data["Airfoil Type"] = None
        wing_section = self.create_rcaide_structure(data_si)

        data["Segment Name"] = self.name_layout.itemAt(2).widget().text()
        return data, wing_section

    def load_data_values(self, section_data):
        self.data_entry_widget.load_data(section_data)
        self.name_layout.itemAt(2).widget().setText(section_data["Segment Name"])

        if ("Airfoil" in section_data):
            file_path = section_data["Airfoil"][0]
            if file_path and file_path.strip():
                self.airfoil_type_combo.setCurrentText("Coordinate File")
                self.file_path_input.setText(file_path)
                self.naca_code_input.setText("")
            else:
                self.airfoil_type_combo.setCurrentText("None")
                self.naca_code_input.setText("")
                self.file_path_input.setText("")
        elif "Airfoil Type" in section_data:
            airfoil_type = section_data.get("Airfoil Type", "None")
            self.airfoil_type_combo.setCurrentText(airfoil_type if airfoil_type else "None")
            self.naca_code_input.setText(section_data.get("Airfoil Code", ""))
            self.file_path_input.setText(section_data.get("Airfoil Coordinate File Path", ""))
        else:
            self.airfoil_type_combo.setCurrentText("None")
            self.naca_code_input.setText("")
            self.file_path_input.setText("")

        self._update_airfoil_ui_state()

    def delete_button_pressed(self): 
        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)

    def read_airfoil_dat_file(self, file_path):
        coordinates = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line or (not line[0].isdigit() and line[0] != '-'):
                        continue
                    try:
                        parts = line.split()
                        if len(parts) >= 2:
                            x = float(parts[0])
                            y = float(parts[1])
                            coordinates.append((x, y))
                    except ValueError: 
                        continue
        except FileNotFoundError:
            print(f"File not found")
            return None
        except Exception as e:
            print(f"Error reading airfoil file")
            return None
        if not coordinates:
            print(f"Warning: No valid coordinates")
            return None
        print("Read successful")
        return coordinates