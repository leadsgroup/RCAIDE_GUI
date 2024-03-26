# ------------------------------------------------------------------------------------------------------------------------------------
#   Imports
# ------------------------------------------------------------------------------------------------------------------------------------

# RCAIDE imports
'''Will use later'''

# QT imports
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QLineEdit, QScrollArea, \
                            QFrame, QComboBox, QSpacerItem, QSizePolicy

from tabs.geometry.frames.geometry_frame import GeometryFrame
from widgets.color import Color
from utilities import Units
from widgets.unit_picker_widget import UnitPickerWidget

# ------------------------------------------------------------------------------------------------------------------------------------
#   Wings
# ------------------------------------------------------------------------------------------------------------------------------------

class WingsFrame(QWidget, GeometryFrame):
    def __init__(self):
        super(WingsFrame, self).__init__()
              
        self.data_fields = {}      
        
        self.unit_options = [
            ("Taper Ratio", Units.Unitless),
            ("Dihedral", Units.Angle),
            ("Aspect Ratio", Units.Unitless),
            ("Thickness to Chord", Units.Unitless),
            ("Aerodynamic Center", Units.Length),
            ("Exposed Root Chord Offset", Units.Length),
            ("Total Length", Units.Length), 
            ("Spans Projected", Units.Length),
            ("Spans Total", Units.Length),
            ("Areas Reference", Units.Area),
            ("Areas Exposed", Units.Area),
            ("Areas Affected", Units.Area), 
            ("Areas Wetted", Units.Area),
            ("Root Chord", Units.Length),
            ("Tip Chord", Units.Length), 
            ("Mean Aerodynamic Chord", Units.Length),
            ("Mean Geometric Chord", Units.Length),
            ("Quarter Chord Sweep Angle", Units.Angle),
            ("Half Chord Sweep Angle", Units.Angle), 
            ("Leading Edge Sweep Angle", Units.Angle), 
            ("Root Chord Twist Angle", Units.Angle),
            ("Tip Chord Twist Angle", Units.Angle)
        ]        
        
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
        wing_name_entry.setFixedWidth(247)
        bold_font = QFont()
        bold_font.setBold(True)
        wing_name_label.setFont(bold_font)        
        header_layout.addWidget(wing_name_label)
        header_layout.addWidget(wing_name_entry)
        header_layout.addStretch(1)

        delete_button = QPushButton("Create New Wing Structure", self)
        delete_button.setFixedWidth(336)        
        delete_button.clicked.connect(self.delete_data)
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
            
            row, col = divmod(index, 2)           
            line_edit = QLineEdit(self)
            line_edit.setFixedWidth(150)
        
            # Find the corresponding unit for this label
            unit_for_label = next((unit for label_option, unit in self.unit_options if label_option == label), None)
        
            if unit_for_label is not None:
                unit_picker = UnitPickerWidget(unit_for_label)
                unit_picker.setFixedWidth(90)           
                
            else:
                continue
        
            grid_layout.addWidget(QLabel(label + ":"), row, col * 3)
            grid_layout.addWidget(line_edit, row, col * 3 + 1, alignment=Qt.AlignmentFlag.AlignLeft)
            grid_layout.addWidget(unit_picker, row, col * 3 + 2, alignment=Qt.AlignmentFlag.AlignLeft)
        
            self.data_fields[label] = (line_edit, unit_picker)
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
        #   Wings Segments / Control Surfaces
        # -------------------------------------------------------------------------------------------------------------------------------
        
        # Wing Section Buttons
        self.additional_layout = QVBoxLayout()
        self.additional_header_layout = QHBoxLayout()
        self.additional_layout.addLayout(self.additional_header_layout)
        self.content_layout.addLayout(self.additional_layout)
    
        add_wing_segment_button = QPushButton("Add Wing Segment", self)
        add_wing_segment_button.clicked.connect(self.add_wing_segment)
        
        sections_buttons_layout = QHBoxLayout()
        self.content_layout.addLayout(sections_buttons_layout)
        sections_buttons_layout.addWidget(add_wing_segment_button)
        
        # Control Surface Buttons
        self.cs_additional_layout = QVBoxLayout()
        self.content_layout.addLayout(self.cs_additional_layout)           
        
        add_cs_button = QPushButton("Add Control Surface", self)     
        add_cs_button.clicked.connect(self.add_control_surface)
        append_button = QPushButton("Save Wing Data", self)
        append_button.clicked.connect(self.append_data)
        
        surface_buttons_layout = QVBoxLayout()
        self.content_layout.addLayout(surface_buttons_layout)
        surface_buttons_layout.addWidget(add_cs_button)  
        surface_buttons_layout.addWidget(append_button)
        
        
    def add_wing_segment(self):
        # Create new QVBoxLayout for the entire section, including the header and data fields
        segment_layout = QVBoxLayout()
        
        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.Shape.HLine)        
        segment_layout.addWidget(horizontal_line)
        horizontal_line.setStyleSheet("color: gray")        
        
        # Section header layout with segment name, append, and delete buttons
        section_header_layout = QHBoxLayout()
    
        bold_font = QFont()
        bold_font.setBold(True)
    
        # Segment Name Label and Entry
        segment_name_label = QLabel("Segment Name:")
        segment_name_label.setFont(bold_font)
        segment_name = QLineEdit(self)
        segment_name.setFixedWidth(225)
    
        # Add segment name label and entry to the header
        section_header_layout.addWidget(segment_name_label)
        section_header_layout.addWidget(segment_name)
        section_header_layout.addStretch(1)
        
        delete_section_button = QPushButton("Delete Wing Segment", self)
        delete_section_button.setFixedWidth(337)
    
        # Connections for append and delete buttons
        delete_section_button.clicked.connect(lambda: print("Delete Wing Section"))
    
        # Add buttons to the header layout
        section_header_layout.addWidget(delete_section_button)        
    
        # Add the header layout to the section layout
        segment_layout.addLayout(section_header_layout)
    
        # Data fields for the wing section
        additional_segment_layout = QGridLayout()     
        
        segment_labels = [
            "Percent Span Location", "Twist", "Root Chord Percent", "Thickness to Chord", "Dihedral Outboard", "Quarter Chord Sweep",
            "Airfoil"
        ]
    
        segment_units = [
            ("Percent Span Location", Units.Unitless),
            ("Twist", Units.Angle),
            ("Root Chord Percent", Units.Unitless),
            ("Thickness to Chord", Units.Unitless),
            ("Dihedral Outboard", Units.Angle),
            ("Quarter Chord Sweep", Units.Angle),
            ("Airfoil", Units.Unitless)
        ]
              
        
        for index, label in enumerate(segment_labels):
            row, col = divmod(index, 2)           
            line_edit = QLineEdit(self)
            line_edit.setFixedWidth(150)
        
            # Find the corresponding unit for this label
            unit_for_label = next((unit for label_option, unit in segment_units if label_option == label), None)
        
            if unit_for_label is not None:
                unit_picker = UnitPickerWidget(unit_for_label)
                unit_picker.setFixedWidth(90)           
        
            else:
                continue
        
            additional_segment_layout.addWidget(QLabel(label + ":"), row, col * 3)
            additional_segment_layout.addWidget(line_edit, row, col * 3 + 1, alignment=Qt.AlignmentFlag.AlignLeft)
            additional_segment_layout.addWidget(unit_picker, row, col * 3 + 2, alignment=Qt.AlignmentFlag.AlignLeft)
        
            self.data_fields[label] = (line_edit, unit_picker)
            self.data_values['wing_' + label] = line_edit

        # Add the grid layout for data fields to the section layout
        segment_layout.addLayout(additional_segment_layout)

        # Add the entire section layout to the additional layout
        self.additional_layout.addLayout(segment_layout)
        
    def add_control_surface(self):
        surface_layout = QVBoxLayout()

        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.Shape.HLine)
        surface_layout.addWidget(horizontal_line)
        horizontal_line.setStyleSheet("color: gray")

        # Section header layout
        surface_header_layout = QHBoxLayout()

        bold_font = QFont()
        bold_font.setBold(True)

        # Control Surface Name Label and Entry
        surface_name_label = QLabel("Control Surface Name:")
        surface_name_label.setFont(bold_font)
        surface_name = QLineEdit(self)
        surface_name.setFixedWidth(196)
        surface_header_layout.addWidget(surface_name_label)
        surface_header_layout.addWidget(surface_name)

        # Control Surface ComboBox
        self.control_surface_combobox = QComboBox()
        self.control_surface_combobox.setFixedWidth(80)
        self.control_surface_combobox.addItems(["Slat", "Flap", "Aileron"])
        surface_header_layout.addWidget(self.control_surface_combobox)
        surface_header_layout.addStretch(1)

        # Delete Button
        delete_section_button = QPushButton("Delete Control Surface", self)
        delete_section_button.setFixedWidth(337)
        delete_section_button.clicked.connect(lambda: print("Delete Control Surface"))
        surface_header_layout.addWidget(delete_section_button)
        surface_layout.addLayout(surface_header_layout)

        # Data fields layout
        self.additional_surface_layout = QGridLayout()
        surface_layout.addLayout(self.additional_surface_layout)

        self.populateDataFields()

        # Connect the combobox signal
        self.control_surface_combobox.currentTextChanged.connect(self.update_visibility)

        self.cs_additional_layout.addLayout(surface_layout)

        # Set initial visibility for Slat fields
        self.update_visibility("Slat")

    def populateDataFields(self):
    # Example data fields for "Slat", "Flap", and "Aileron"
        data_fields = [
            ("Slat: Span Fraction Start:", "Slat"),
            ("Slat: Span Fraction End:", "Slat"),
            ("Slat: Deflection:", "Slat"),
            ("Slat: Chord Fraction:", "Slat"),
            ("Aileron: Span Fraction Start:", "Aileron"),
            ("Aileron: Span Fraction End:", "Aileron"),
            ("Aileron: Deflection:", "Aileron"),
            ("Aileron: Chord Fraction:", "Aileron"),            
            ("Flap: Span Fraction Start:", "Flap"),
            ("Flap: Span Fraction End:", "Flap"),
            ("Flap: Deflection:", "Flap"),
            ("Flap: Chord Fraction:", "Flap"),
            ("Flap: Configuration:", "Flap"),
        ]
    
        for index, (label_text, control_surface) in enumerate(data_fields):
            row, col = divmod(index, 2)  # Calculate row, column for two-column layout
            label = QLabel(label_text)
            field = QLineEdit(self)
            field.setFixedWidth(150)
            unit_combobox = QComboBox()
            unit_combobox.addItems(["degrees", "rad"] if "Deflection" in label_text else ["NA"])
            unit_combobox.setFixedWidth(80)
    
            # Add label, field, and combobox to the grid; adjust col * 3 to fit two-column layout
            self.additional_surface_layout.addWidget(label, row, col * 6)  # Adjust multiplier for label placement
            self.additional_surface_layout.addWidget(field, row, col * 6 + 1)  # Next to label
            self.additional_surface_layout.addWidget(unit_combobox, row, col * 6 + 2, alignment=Qt.AlignmentFlag.AlignLeft)
    
            # Initially set all widgets to invisible; visibility is controlled by combobox selection
            label.setVisible(False)
            field.setVisible(False)
            unit_combobox.setVisible(False)
    
            # Tag widgets with their control surface for easier identification during updates
            label.setProperty("control_surface", control_surface)
            field.setProperty("control_surface", control_surface)
            unit_combobox.setProperty("control_surface", control_surface)

    def update_visibility(self, selected_surface):
        # Iterate through all widgets in the layout and update visibility based on the control surface
        for i in range(self.additional_surface_layout.count()):
            widget = self.additional_surface_layout.itemAt(i).widget()
            if widget and widget.property("control_surface") == selected_surface:
                widget.setVisible(True)
            elif widget:
                widget.setVisible(False)

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