# RCAIDE_GUI/tabs/geometry/widgets/nacelle/nacelle_section_widget.py
# 
# Created:  Dec 2025, M. Clarke 

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
# RCAIDE imports   
import RCAIDE

from tabs.geometry.widgets import GeometryDataWidget
# RCAIDE GUI imports
from utilities import Units
from widgets import DataEntryWidget

# PyQT imports  
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget, \
    QFrame


# ----------------------------------------------------------------------------------------------------------------------
#  Nacelle Section Widget 
# ---------------------------------------------------------------------------------------------------------------------- 
class NacelleSectionWidget(GeometryDataWidget):
    def __init__(self, index, on_delete, section_data=None):
        super(NacelleSectionWidget, self).__init__()

        # self.data_fields = {}
        self.coordinate_filename = ""
        self.index = index
        self.on_delete = on_delete
        self.data_entry_widget: DataEntryWidget | None = None

        self.name_layout = QHBoxLayout()
        self.init_ui(section_data)

    # noinspection DuplicatedCode
    def init_ui(self, section_data):
        main_layout = QVBoxLayout()
        # add spacing
        spacer_left = QSpacerItem(
            80, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(
            300, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_layout.addItem(spacer_left)
        self.name_layout.addWidget(QLabel("Segment Name: "))
        self.name_layout.addWidget(QLineEdit(self))
        self.name_layout.addItem(spacer_right)

        main_layout.addLayout(self.name_layout)

        # List of data labels
        data_units_labels = [
            ("Percent X Location", Units.Unitless),
            ("Percent Z Location", Units.Unitless),
            ("Height", Units.Length),
            ("Width", Units.Length),
        ]

        self.data_entry_widget = DataEntryWidget(data_units_labels)
        delete_button = QPushButton("Delete Section", self)
        delete_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        delete_button.setFixedWidth(150)
        delete_button.clicked.connect(self.delete_button_pressed)

        # center delete button
        delete_button_layout = QHBoxLayout()
        delete_button_layout.addItem(QSpacerItem(
            50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        delete_button_layout.addWidget(delete_button)
        delete_button_layout.addItem(QSpacerItem(
            50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        main_layout.addWidget(self.data_entry_widget)
        main_layout.addLayout(delete_button_layout)

        # Add horizontal bar
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line_bar)

        if section_data:
            self.load_data_values(section_data)

        self.setLayout(main_layout)

    def create_rcaide_structure(self, data):
        segment = RCAIDE.Library.Components.Nacelles.Segments.Segment()
        segment.percent_x_location = data["Percent X Location"][0]
        segment.percent_z_location = data["Percent Z Location"][0]
        segment.height = data["Height"][0]
        segment.width = data["Width"][0]
        segment.tag = data["Segment Name"]

        return segment

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data["Segment Name"] = self.name_layout.itemAt(2).widget().text()
        data_si["Segment Name"] = self.name_layout.itemAt(2).widget().text()

        segment = self.create_rcaide_structure(data_si)
        return data, segment

    def load_data_values(self, data):
        pass

    def delete_button_pressed(self):
        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)
