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
        
        # List to store data values for additional wing sections
        self.additional_data_values = []

        # Create the main layout for the content
        self.content_layout = QVBoxLayout() 
        self.setLayout(self.content_layout)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Header layout with bold label and buttons
        header_layout = QHBoxLayout()
        wing_name_label = QLabel("Wing Name:")
        wing_name_entry = QLineEdit(self)
        wing_name_entry.setFixedWidth(255)
        bold_font = QFont()
        bold_font.setBold(True)
        wing_name_label.setFont(bold_font)        
        header_layout.addWidget(wing_name_label)
        header_layout.addWidget(wing_name_entry)

        append_button = QPushButton("Save Wing Data", self)
        delete_button = QPushButton("Delete Wing Data", self)
        append_button.setFixedWidth(346)
        delete_button.setFixedWidth(346)        
        append_button.clicked.connect(self.append_data)
        delete_button.clicked.connect(self.delete_data)
        header_layout.addWidget(append_button)
        header_layout.addWidget(delete_button)
        self.content_layout.addLayout(header_layout)

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
        self.content_layout.addLayout(grid_layout)

        # -------------------------------------------------------------------------------------------------------------------------------
        #   Wings Sections
        # -------------------------------------------------------------------------------------------------------------------------------
        
        self.additional_layout = QVBoxLayout()
        self.additional_header_layout = QHBoxLayout()
        self.additional_layout.addLayout(self.additional_header_layout)
        self.content_layout.addLayout(self.additional_layout)
        add_wing_section_button = QPushButton("Add Wing Section", self)
        append_all_section_button = QPushButton("Append All Wing Section Data", self)
        add_cs_button = QPushButton("Add Control Surface", self)
        append_all_cs_button = QPushButton("Append All C.S. Data", self)
        
        ''''''
        '''alter'''
        ''''''
        
        add_wing_section_button.clicked.connect(self.add_wing_section)
        append_all_section_button.clicked.connect(self.append_all_data)
        #add_cs_button.clicked.connect(self.add_cs_section)
        append_all_cs_button.clicked.connect(self.append_all_data)
        
        buttons_layout = QHBoxLayout()
        self.content_layout.addLayout(buttons_layout)
        
        buttons_layout.addWidget(add_wing_section_button)
        buttons_layout.addWidget(append_all_section_button)
        buttons_layout.addWidget(add_cs_button)
        buttons_layout.addWidget(append_all_cs_button)    
        
    def add_wing_section(self):
        # Create new QVBoxLayout for the entire section, including the header and data fields
        section_layout = QVBoxLayout()
        section_layout.addSpacing(15)
        
        # Section header layout with segment name, append, and delete buttons
        section_header_layout = QHBoxLayout()
    
        bold_font = QFont()
        bold_font.setBold(True)
    
        # Segment Name Label and Entry
        segment_name_label = QLabel("Segment Name:")
        segment_name_label.setFont(bold_font)
        segment_name = QLineEdit(self)
        segment_name.setFixedWidth(233)
    
        # Add segment name label and entry to the header
        section_header_layout.addWidget(segment_name_label)
        section_header_layout.addWidget(segment_name)
    
        # Append and Delete buttons for this wing section
        append_data_button = QPushButton("Save Wing Section Data", self)
        delete_section_button = QPushButton("Delete Wing Section", self)
        append_data_button.setFixedWidth(346)
        delete_section_button.setFixedWidth(346)
    
        # Connections for append and delete buttons
        append_data_button.clicked.connect(lambda: print("Append Section Data"))
        delete_section_button.clicked.connect(lambda: print("Delete Section"))
    
        # Add buttons to the header layout
        section_header_layout.addWidget(append_data_button)
        section_header_layout.addWidget(delete_section_button)
    
        # Add the header layout to the section layout
        section_layout.addLayout(section_header_layout)
    
        # Data fields for the wing section
        additional_section_layout = QGridLayout()
    
        # Adding data fields
        labels_and_fields = [
            ("Percent Span Location:", QLineEdit(self)),
            ("Twist:", QLineEdit(self)),
            ("Root Chord Percent:", QLineEdit(self)),
            ("Thickness to Chord:", QLineEdit(self)),
            ("Dihedral Outboard:", QLineEdit(self)),
            ("Quarter Chord Sweep:", QLineEdit(self)),
            ("Airfoil:", QLineEdit(self)),
        ]
    
        for i, (label_text, field) in enumerate(labels_and_fields):
            label = QLabel(label_text)
            field.setFixedWidth(100)
            row, col = divmod(i, 3)
            additional_section_layout.addWidget(label, row, col * 2)
            additional_section_layout.addWidget(field, row, col * 2 + 1)
    
        # Add the grid layout for data fields to the section layout
        section_layout.addLayout(additional_section_layout)
    
        # Add the entire section layout to the additional layout
        self.additional_layout.addLayout(section_layout)


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
        content_widget.setLayout(self.content_layout)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)   

    '''Functions subject to change due to RCAIDE integration''' 

    def append_data(self):
        """Append data action."""
        entered_data = self.get_data_values()
        print("Appending Data:", entered_data)

    def delete_data(self):
        """Delete data action."""
        entered_data = self.get_data_values()
        print("Deleting Data:", entered_data)
        for line_edit in self.data_values.values():
            line_edit.clear()

    def get_data_values(self):
        """ Retrieve data values from line edits."""
        return {label: float(line_edit.text()) if line_edit.text() else 0.0 for label, line_edit in
                self.data_values.items()} 
    
    def delete_and_display_data(self):
        """Combining display_data and delete_section function so button can call both."""
        self.delete_section()
        self.display_data()    
    
    def append_all_data(self):
        """Append the entered data for the additional wing section."""
        all_entered_data = self.get_all_data_values()
        print("Appending All Data:", all_entered_data)    