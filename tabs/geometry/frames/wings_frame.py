# ------------------------------------------------------------------------------------------------------------------------------------
#   Imports
# ------------------------------------------------------------------------------------------------------------------------------------

# RCAIDE imports
'''Will use later'''

# QT imports
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QLineEdit, QScrollArea, QFrame

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
        wing_data_labels = ["Taper Ratio", "Dihedral", "Aspect Ratio", "Thickness to Chord", "Aerodynamic Center",
                            "Exposed Root Chord Offset", "Total Length", "Spans Projected", "Spans Total", "Areas Reference",
                            "Areas Exposed", "Areas Affected", "Areas Wetted", "Root Chord", "Tip Chord", "Mean Aerodynamic Chord",
                            "Mean Geometric Chord", "Quarter Chord Sweep Angle", "Half Chord Sweep Angle", "Leading Edge Sweep Angle",
                            "Root Chord Twist Angle", "Tip Chord Twist Angle"]

        for index, label in enumerate(wing_data_labels):
            row, col = divmod(index, 3)
            line_edit = QLineEdit(self)
            line_edit.setFixedWidth(100)
            grid_layout.addWidget(QLabel(label + ":"), row, col * 2)
            grid_layout.addWidget(line_edit, row, col * 2 + 1)
            self.data_values['wing_' + label] = line_edit
        self.content_layout.addLayout(grid_layout)
        
        # Scroll area setup
        content_widget = QWidget()
        content_widget.setLayout(self.content_layout)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout) 

        # -------------------------------------------------------------------------------------------------------------------------------
        #   Wings Sections / Control Surfaces
        # -------------------------------------------------------------------------------------------------------------------------------
        
        # Wing Section Buttons
        self.additional_layout = QVBoxLayout()
        self.additional_header_layout = QHBoxLayout()
        self.additional_layout.addLayout(self.additional_header_layout)
        self.content_layout.addLayout(self.additional_layout)     
    
        add_wing_section_button = QPushButton("Add Wing Segment", self)
        append_all_section_button = QPushButton("Append All Wing Segment Data", self)
        add_wing_section_button.clicked.connect(self.add_wing_section)
        append_all_section_button.clicked.connect(self.append_all_data)
        
        sections_buttons_layout = QHBoxLayout()
        self.content_layout.addLayout(sections_buttons_layout)
        sections_buttons_layout.addWidget(add_wing_section_button)
        sections_buttons_layout.addWidget(append_all_section_button) 
        
        # Control Surface Buttons
        self.cs_additional_layout = QVBoxLayout()
        self.content_layout.addLayout(self.cs_additional_layout)           
        
        add_cs_button = QPushButton("Add Control Surface", self)
        append_all_cs_button = QPushButton("Append All C.S. Data", self)        
        add_cs_button.clicked.connect(self.add_control_surface)
        append_all_cs_button.clicked.connect(self.append_all_data)     
        
        surface_buttons_layout = QHBoxLayout()
        self.content_layout.addLayout(surface_buttons_layout)
        surface_buttons_layout.addWidget(add_cs_button)
        surface_buttons_layout.addWidget(append_all_cs_button)         
        
        
    def add_wing_section(self):
        # Create new QVBoxLayout for the entire section, including the header and data fields
        section_layout = QVBoxLayout()
        
        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.Shape.HLine)        
        section_layout.addWidget(horizontal_line)
        horizontal_line.setStyleSheet("color: gray;")        
        
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
        append_data_button = QPushButton("Save Wing Segment Data", self)
        delete_section_button = QPushButton("Delete Wing Segment", self)
        append_data_button.setFixedWidth(346)
        delete_section_button.setFixedWidth(346)
    
        # Connections for append and delete buttons
        '''Change'''
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
        
    def add_control_surface(self):
        
        surface_layout = QVBoxLayout()
        
        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.Shape.HLine)        
        surface_layout.addWidget(horizontal_line)
        horizontal_line.setStyleSheet("color: gray")    
        
        # Section header layout with segment name, append, and delete buttons
        surface_header_layout = QHBoxLayout()
        
        bold_font = QFont()
        bold_font.setBold(True)
    
        # Segment Name Label and Entry
        surface_name_label = QLabel("Control Surface Name:")
        surface_name_label.setFont(bold_font)
        surface_name = QLineEdit(self)
        surface_name.setFixedWidth(197)
    
        # Add segment name label and entry to the header
        surface_header_layout.addWidget(surface_name_label)
        surface_header_layout.addWidget(surface_name)
    
        # Append and Delete buttons for this wing section
        append_data_button = QPushButton("Save Control Surface Data", self)
        delete_section_button = QPushButton("Delete Control Surface", self)
        append_data_button.setFixedWidth(346)
        delete_section_button.setFixedWidth(346)
    
        # Connections for append and delete buttons
        append_data_button.clicked.connect(lambda: print("Append Section Data"))
        delete_section_button.clicked.connect(lambda: print("Delete Section"))
    
        # Add buttons to the header layout
        surface_header_layout.addWidget(append_data_button)
        surface_header_layout.addWidget(delete_section_button)
    
        # Add the header layout to the section layout
        surface_layout.addLayout(surface_header_layout)
    
        # Data fields for the wing section
        additional_surface_layout = QGridLayout()     
        
        labels_and_fields = [("Flap: Span Fraction Start:", QLineEdit(self)),
                             ("Slat: Span Fraction Start:", QLineEdit(self)),
                             ("Aileron: Span Fraction Start:", QLineEdit(self)),
                             ("Flap: Span Fraction End:", QLineEdit(self)),
                             ("Slat: Span Fraction End:", QLineEdit(self)),
                             ("Aileron: Span Fraction End:", QLineEdit(self)),
                             ("Flap: Deflection:", QLineEdit(self)),
                             ("Slat: Deflection:", QLineEdit(self)),
                             ("Aileron: Deflection:", QLineEdit(self)),
                             ("Flap: Chord Fraction:", QLineEdit(self)),
                             ("Slat: Chord Fraction:", QLineEdit(self)),
                             ("Aileron: Chord Fraction:", QLineEdit(self)),
                             ("Flap: Configuration:", QLineEdit(self)),]
    
        for i, (label_text, field) in enumerate(labels_and_fields):
            label = QLabel(label_text)
            field.setFixedWidth(100)
            row, col = divmod(i, 3)
            additional_surface_layout.addWidget(label, row, col * 2)
            additional_surface_layout.addWidget(field, row, col * 2 + 1)    
            
        # Add the grid layout for data fields to the section layout
        surface_layout.addLayout(additional_surface_layout)
    
        # Add the entire section layout to the additional layout
        self.cs_additional_layout.addLayout(surface_layout)

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