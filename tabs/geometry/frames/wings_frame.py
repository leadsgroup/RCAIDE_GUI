# ------------------------------------------------------------------------------------------------------------------------------------
#   Imports
# ------------------------------------------------------------------------------------------------------------------------------------

# RCAIDE imports
# '''Will use later'''

# QT imports
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QDoubleValidator, QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QLineEdit, QMessageBox, \
    QScrollArea

from tabs.geometry.frames.geometry_frame import GeometryFrame
from widgets.color import Color


# ------------------------------------------------------------------------------------------------------------------------------------
#   Wings
# ------------------------------------------------------------------------------------------------------------------------------------

class WingsFrame(QWidget, GeometryFrame):
    def __init__(self):
        super(WingsFrame, self).__init__()

        # (Temporary) dictionary to store the entered values
        self.data_values = {}

        # Create the main layout for the content
        content_layout = QVBoxLayout()

        # Header layout with bold label and buttons
        header_layout = QHBoxLayout()
        wing_title_label = QLabel("Add Wing Component")
        bold_font = QFont()
        bold_font.setBold(True)
        wing_title_label.setFont(bold_font)
        header_layout.addWidget(wing_title_label)

        append_button = QPushButton("Append Wing Data", self)
        delete_button = QPushButton("Delete Wing Data", self)
        append_button.clicked.connect(self.append_data)
        delete_button.clicked.connect(self.delete_data)
        header_layout.addWidget(append_button)
        header_layout.addWidget(delete_button)
        content_layout.addLayout(header_layout)
        content_layout.addWidget(Color("lightblue"))

        # Grid layout for wing components
        grid_layout = QGridLayout()
        wing_data_labels = ["Wing Name", "Taper Ratio", "Dihedral", "Aspect Ratio", "Thickness to Chord",
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
            line_edit.setValidator(QDoubleValidator())
            line_edit.setFixedWidth(100)
            grid_layout.addWidget(QLabel(label + ":"), row, col * 2)
            grid_layout.addWidget(line_edit, row, col * 2 + 1)
            self.data_values['wing_' + label] = line_edit
        content_layout.addLayout(grid_layout)

        # -------------------------------------------------------------------------------------------------------------------------------
        #   Preliminary Wing Shape Simulation
        # -------------------------------------------------------------------------------------------------------------------------------        

        # -------------------------------------------------------------------------------------------------------------------------------
        #   Control Surfaces
        # -------------------------------------------------------------------------------------------------------------------------------

        # Spacing before control surface components
        content_layout.addSpacing(20)

        # Layout for control surface components with bold label
        lower_layout = QHBoxLayout()
        cs_title_label = QLabel("Add Control Surface Component")
        cs_title_label.setFont(bold_font)  # Apply the bold font to the label
        lower_layout.addWidget(cs_title_label)

        '''Add commands to these buttons later'''

        append_button2 = QPushButton("Append Control Surface Data", self)
        delete_button2 = QPushButton("Delete Control Surface Data", self)
        lower_layout.addWidget(append_button2)
        lower_layout.addWidget(delete_button2)
        content_layout.addLayout(lower_layout)

        # Grid layout for control surface components
        cs_grid_layout = QGridLayout()
        cs_data_labels = ["Flap: Span Fraction Start", "Slat: Span Fraction Start", "Aileron: Span Fraction Start",
                          "Flap: Span Fraction End", "Slat: Span Fraction End", "Aileron: Span Fraction End",
                          "Flap: Deflection", "Slat: Deflection", "Aileron: Deflection",
                          "Flap: Chord Fraction", "Slat: Chord Fraction", "Aileron: Chord Fraction",
                          "Flap: Configuration"]

        for index, label in enumerate(cs_data_labels):
            row, col = divmod(index, 3)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())
            line_edit.setFixedWidth(100)
            cs_grid_layout.addWidget(QLabel(label + ":"), row, col * 2)
            cs_grid_layout.addWidget(line_edit, row, col * 2 + 1)
            self.data_values['cs_' + label] = line_edit
        content_layout.addLayout(cs_grid_layout)

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

    def show_popup(self, message, parent):
        """ Show a pop-up message. """
        popup = QMessageBox(parent)
        popup.setWindowTitle("Info")
        popup.setText(message)
        popup.setStyleSheet("QLabel{min-width: 300px;}")
        popup.show()
        timer = QTimer(popup)
        timer.setSingleShot(True)
        timer.timeout.connect(popup.close)
        timer.start(2000)

        # -------------------------------------------------------------------------------------------------------------------------------
        #   Wing Sections
        # -------------------------------------------------------------------------------------------------------------------------------

    def add_wing_section(self):
        """Add a new fuselage section with input boxes for Percent X Location, Percent Z Location, Height, and Width."""
        additional_section_layout = QGridLayout()

        percent_x_location = QLineEdit(self)
        percent_x_location.setValidator(QDoubleValidator())
        percent_x_location.setFixedWidth(100)

        percent_z_location = QLineEdit(self)
        percent_z_location.setValidator(QDoubleValidator())
        percent_z_location.setFixedWidth(100)

        height = QLineEdit(self)
        height.setValidator(QDoubleValidator())
        height.setFixedWidth(100)

        width = QLineEdit(self)
        width.setValidator(QDoubleValidator())
        width.setFixedWidth(100)

        additional_section_layout.addWidget(QLabel("Percent X Location:"), 0, 0)
        additional_section_layout.addWidget(percent_x_location, 0, 1)

        additional_section_layout.addWidget(QLabel("Percent Z Location:"), 1, 0)
        additional_section_layout.addWidget(percent_z_location, 1, 1)

        additional_section_layout.addWidget(QLabel("Height:"), 0, 2)
        additional_section_layout.addWidget(height, 0, 3)

        additional_section_layout.addWidget(QLabel("Width:"), 1, 2)
        additional_section_layout.addWidget(width, 1, 3)

        # delete_section_button = QPushButton("Delete Fuselage Section", self)
        # append_data_button = QPushButton("Append Fuselage Section Data", self)
