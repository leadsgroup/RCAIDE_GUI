# ------------------------------------------------------------------------------------------------------------------------------------
#   Imports
# ------------------------------------------------------------------------------------------------------------------------------------

# RCAIDE imports
'''Will use later'''

# QT imports
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QDoubleValidator, QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QLineEdit, QMessageBox, \
    QScrollArea

from widgets.color import Color


# ------------------------------------------------------------------------------------------------------------------------------------
#   Wings
# ------------------------------------------------------------------------------------------------------------------------------------

class WingsFrame(QWidget):
    def __init__(self):
        super(WingsFrame, self).__init__()

        # (Temporary) dictionary to store the entered values
        self.data_values = {}

        # Create the main layout for the content
        content_layout = QVBoxLayout() 
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Header layout with bold label and buttons
        header_layout = QHBoxLayout()
        wing_name_label = QLabel("Wing Name:")
        wing_name_entry = QLineEdit(self)
        wing_name_entry.setFixedWidth(265)
        bold_font = QFont()
        bold_font.setBold(True)
        wing_name_label.setFont(bold_font)        
        header_layout.addWidget(wing_name_label)
        header_layout.addWidget(wing_name_entry)

        append_button = QPushButton("Append Wing Data", self)
        delete_button = QPushButton("Delete Wing Data", self)
        append_button.setFixedWidth(341)
        delete_button.setFixedWidth(341)        
        append_button.clicked.connect(self.append_data)
        delete_button.clicked.connect(self.delete_data)
        header_layout.addWidget(append_button)
        header_layout.addWidget(delete_button)
        content_layout.addLayout(header_layout)

        # Grid layout for wing components
        grid_layout = QGridLayout()
        wing_data_labels = ["Taper Ratio", "Dihedral", "Aspect Ratio", "Thickness to Chord",
                            "Aerodynamic Center",
                            "Exposed Root Chord Offset", "Total Length", "Spans Projected", "Spans Total",
                            "Areas Reference",
                            "Areas Exposed", "Areas Affected", "Areas Wetted", "Root Chord", "Tip Chord",
                            "Mean Aerodynamic Chord",
                            "Mean Geometric Chord", "Quarter Chord Sweep Angle", "Half Chord Sweep Angle",
                            "Leading Edge Sweep Angle",
                            "Root Chord Twist Angle", "Tip Chord Twist Angle"]

        for index, label in enumerate(wing_data_labels):
            row, col = divmod(index, 3)
            line_edit = QLineEdit(self)
            line_edit.setFixedWidth(100)
            grid_layout.addWidget(QLabel(label + ":"), row, col * 2)
            grid_layout.addWidget(line_edit, row, col * 2 + 1)
            self.data_values['wing_' + label] = line_edit
        content_layout.addLayout(grid_layout)

        add_wing_section_button = QPushButton("Add Wing Section", self)
        append_all_section_button = QPushButton("Append All Wing Section Data", self)
        add_cs_button = QPushButton("Add Control Surface", self)
        append_all_cs_button = QPushButton("Append All C.S. Data", self)
        
        ''''''
        '''alter'''
        ''''''
        
        #add_wing_section_button.clicked.connect(self.append_data)
        #append_all_section_button.clicked.connect(self.append_data)
        #add_cs_button.clicked.connect(self.delete_data)
        #append_all_cs_button.clicked.connect(self.delete_data)
        
        buttons_layout = QHBoxLayout()
        content_layout.addLayout(buttons_layout)
        
        buttons_layout.addWidget(add_wing_section_button)
        buttons_layout.addWidget(append_all_section_button)
        buttons_layout.addWidget(add_cs_button)
        buttons_layout.addWidget(append_all_cs_button)

        # -------------------------------------------------------------------------------------------------------------------------------
        #   Wings Sections
        # -------------------------------------------------------------------------------------------------------------------------------

        #self.add_section_button = QPushButton("Add Wing Section", self)
        #self.add_section_button.clicked.connect(self.add_wing_section)
        #self.content_layout.addWidget(self.add_section_button)        
        
    #def add_wing_section(self):
        #"""Add a new wing section"""
        #additional_wing_section_layout = QGridLayout()
        
        #segment_name = QLineEdit(self)
        #segment_name.setFixedWidth(100)
        
        #percent_span_location = QLineEdit(self)
        #percent_span_location.setFixedWidth(100)
        
        #twist = QLineEdit(self)
        #twist.setFixedWidth(100)
        
        #root_chord_percent = QLineEdit(self)
        #root_chord_percent.setFixedWidth(100)
        
        #thickness_to_chord = QLineEdit(self)
        #thickness_to_chord.setFixedWidth(100)
        
        #dihedral_outboard = QLineEdit(self)
        #dihedral_outboard.setFixedWidth(100)
        
        #quarter_chord_sweep = QLineEdit(self)
        #quarter_chord_sweep.setFixedWidth(100)
        
        #airfoil = QLineEdit(self)
        #airfoil.setFixedWidth(100)
        
        #additional_wing_section_layout.addWidget(QLabel("Segment Name:"), 0, 0)
        #additional_wing_section_layout.addWidget(segment_name, 0, 1)

        #additional_wing_section_layout.addWidget(QLabel("Percent Span Location:"), 1, 0)
        #additional_wing_section_layout.addWidget(percent_span_location, 1, 1)

        #additional_wing_section_layout.addWidget(QLabel("Twist:"), 0, 2)
        #additional_wing_section_layout.addWidget(twist, 0, 3)

        #additional_wing_section_layout.addWidget(QLabel("Root Chord Percent:"), 1, 2)
        #additional_wing_section_layout.addWidget(root_chord_percent, 1, 3)  
        
        #additional_wing_section_layout.addWidget(QLabel("Thickness to Chord:"), 2, 0)
        #additional_wing_section_layout.addWidget(thickness_to_chord, 2, 1)

        #additional_wing_section_layout.addWidget(QLabel("Dihedral Outboard:"), 2, 2)
        #additional_wing_section_layout.addWidget(dihedral_outboard, 2, 3)

        #additional_wing_section_layout.addWidget(QLabel("Quarter Chord Sweep:"), 3, 0)
        #additional_wing_section_layout.addWidget(quarter_chord_sweep, 3, 1)

        #additional_wing_section_layout.addWidget(QLabel("Airfoil:"), 3, 2)
        #additional_wing_section_layout.addWidget(airfoil, 3, 3)   
        
        #delete_section_button = QPushButton("Delete Wing Section", self)
        #append_data_button = QPushButton("Append Wing Section Data", self)  
        
        #delete_section_button.clicked.connect(self.delete_and_display_data)
        #append_data_button.clicked.connect(lambda _, index=len(self.additional_data_values): self.append_section_data(index))        

        # -------------------------------------------------------------------------------------------------------------------------------
        #   Control Surfaces
        # -------------------------------------------------------------------------------------------------------------------------------

        ## Spacing before control surface components
        #content_layout.addSpacing(20)

        ## Layout for control surface components with bold label
        #lower_layout = QHBoxLayout()
        #cs_title_label = QLabel("Add Control Surface Component")
        #cs_title_label.setFont(bold_font)
        #lower_layout.addWidget(cs_title_label)

        #'''Add commands to these buttons later'''
        
        #append_button2 = QPushButton("Append Control Surface Data", self)
        #delete_button2 = QPushButton("Delete Control Surface Data", self)
        #append_button2.setFixedWidth(341)
        #delete_button2.setFixedWidth(341)         
        #lower_layout.addWidget(append_button2)
        #lower_layout.addWidget(delete_button2)
        #content_layout.addLayout(lower_layout)

        ## Grid layout for control surface components
        #cs_grid_layout = QGridLayout()
        #cs_data_labels = ["Flap: Span Fraction Start", "Slat: Span Fraction Start", "Aileron: Span Fraction Start",
                          #"Flap: Span Fraction End", "Slat: Span Fraction End", "Aileron: Span Fraction End",
                          #"Flap: Deflection", "Slat: Deflection", "Aileron: Deflection",
                          #"Flap: Chord Fraction", "Slat: Chord Fraction", "Aileron: Chord Fraction",
                          #"Flap: Configuration"]

        #for index, label in enumerate(cs_data_labels):
            #row, col = divmod(index, 3)
            #line_edit = QLineEdit(self)
            #line_edit.setFixedWidth(100)
            #cs_grid_layout.addWidget(QLabel(label + ":"), row, col * 2)
            #cs_grid_layout.addWidget(line_edit, row, col * 2 + 1)
            #self.data_values['cs_' + label] = line_edit
        #content_layout.addLayout(cs_grid_layout)

        # Scroll area setup
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)   

    '''Functions subject to change due to RCAIDE integration''' 

    def append_data(self):
        """ Append data action. """
        entered_data = self.get_data_values()
        print("Appending Data:", entered_data)
        self.show_popup("Data Saved!", self)

    def delete_data(self):
        """ Delete data action. """
        entered_data = self.get_data_values()
        print("Deleting Data:", entered_data)
        for line_edit in self.data_values.values():
            line_edit.clear()
        self.show_popup("Data Erased!", self)

    def get_data_values(self):
        """ Retrieve data values from line edits. """
        return {label: float(line_edit.text()) if line_edit.text() else 0.0 for label, line_edit in
                self.data_values.items()} 