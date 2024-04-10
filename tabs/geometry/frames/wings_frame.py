# ------------------------------------------------------------------------------------------------------------------------------------
#   Imports
# ------------------------------------------------------------------------------------------------------------------------------------

# RCAIDE imports
'''Will use later'''

# QT imports
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QLineEdit, QScrollArea, \
    QFrame

from tabs.geometry.frames.geometry_frame import GeometryFrame
from utilities import Units
from widgets.data_entry_widget import DataEntryWidget


# ------------------------------------------------------------------------------------------------------------------------------------
#   Wings
# ------------------------------------------------------------------------------------------------------------------------------------

class WingsFrame(QWidget, GeometryFrame):
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

        self.content_layout.addLayout(header_layout)

        data_units_labels = [
            ("Taper Ratio", Units.Unitless),
            ("Dihedral", Units.Angle),
            ("Aspect Ratio", Units.Unitless),
            ("Thickness to Chord", Units.Unitless),
            ("Aerodynamic Center", Units.Unitless),
            ("Exposed Root Chord Offset", Units.Unitless),
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

        self.data_entry_widget : DataEntryWidget = DataEntryWidget(data_units_labels)
        self.content_layout.addWidget(self.data_entry_widget)

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
        save_button = QPushButton("Save Wing Data", self)
        add_wing_section_button.clicked.connect(self.add_wing_section)
        save_button.clicked.connect(self.append_all_data)

        # Control Surface Buttons
        self.cs_additional_layout = QVBoxLayout()
        self.content_layout.addLayout(self.cs_additional_layout)

        add_cs_button = QPushButton("Add Control Surface", self)
        append_all_cs_button = QPushButton("Save Control Surface Data", self)
        add_cs_button.clicked.connect(self.add_control_surface)
        append_all_cs_button.clicked.connect(self.append_all_data)

        sections_buttons_layout = QHBoxLayout()
        sections_buttons_layout.addWidget(add_wing_section_button)
        sections_buttons_layout.addWidget(save_button)
        sections_buttons_layout.addWidget(add_cs_button)
        sections_buttons_layout.addWidget(append_all_cs_button)
        self.content_layout.addLayout(sections_buttons_layout)

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

        data_units_labels = [
            ("Percent Span Location", Units.Unitless),
            ("Twist", Units.Angle),
            ("Root Chord Percent", Units.Unitless),
            ("Thickness to Chord", Units.Unitless),
            ("Dihedral Outboard", Units.Angle),
            ("Quarter Chord Sweep", Units.Angle),
            ("Airfoil", Units.Unitless),
        ]

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

        data_units_labels = [
            ("Flap: Span Fraction Start", Units.Unitless),
            ("Slat: Span Fraction Start", Units.Unitless),
            ("Aileron: Span Fraction Start", Units.Unitless),
            ("Flap: Span Fraction End", Units.Unitless),
            ("Slat: Span Fraction End", Units.Unitless),
            ("Aileron: Span Fraction End", Units.Unitless),
            ("Flap: Deflection", Units.Angle),
            ("Slat: Deflection", Units.Angle),
            ("Aileron: Deflection", Units.Angle),
            ("Flap: Chord Fraction", Units.Unitless),
            ("Slat: Chord Fraction", Units.Unitless),
            ("Aileron: Chord Fraction", Units.Unitless),
            ("Flap: Configuration", Units.Unitless),
        ]

        cs_data_entry_widget = DataEntryWidget(data_units_labels)
        # Add the grid layout for data fields to the section layout
        surface_layout.addWidget(cs_data_entry_widget)

        # Add the entire section layout to the additional layout
        self.cs_additional_layout.addLayout(surface_layout)

    def save_data(self):
        """Append data action."""
        entered_data = self.get_data_values()
        print("Save Data:", entered_data)

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
