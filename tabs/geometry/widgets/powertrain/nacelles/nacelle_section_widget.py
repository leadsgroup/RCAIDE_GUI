# RCAIDE_GUI/tabs/geometry/widgets/powertrain/nacelles/nacelle_section_widget.py

# Created: Dec 2025, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
# RCAIDE imports
import RCAIDE

from tabs.geometry.widgets import GeometryDataWidget
# RCAIDE GUI imports
from utilities import Units
from common_widgets import DataEntryWidget

# PyQT imports
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget, QFrame, QComboBox,
)
from PyQt6.QtCore import Qt


# ----------------------------------------------------------------------------------------------------------------------
#  Nacelle Section Widget
# ----------------------------------------------------------------------------------------------------------------------
class NacelleSectionWidget(GeometryDataWidget):
    _SEGMENT_TYPES = [
        "Circle Segment",
        "Ellipse Segment",
        "Rounded Rectangle Segment",
        "Super Ellipse Segment",
        "Segment",
    ]

    _RCAIDE_SEGMENT_CLASS = {
        "Circle Segment":            lambda: RCAIDE.Library.Components.Nacelles.Segments.Circle_Segment(),
        "Ellipse Segment":           lambda: RCAIDE.Library.Components.Nacelles.Segments.Ellipse_Segment(),
        "Rounded Rectangle Segment": lambda: RCAIDE.Library.Components.Nacelles.Segments.Rounded_Rectangle_Segment(),
        "Super Ellipse Segment":     lambda: RCAIDE.Library.Components.Nacelles.Segments.Super_Ellipse_Segment(),
        "Segment":                   lambda: RCAIDE.Library.Components.Nacelles.Segments.Segment(),
    }

    def __init__(self, index, on_delete, section_data=None):
        super(NacelleSectionWidget, self).__init__()

        self.coordinate_filename = ""
        self.index = index
        self.on_delete = on_delete
        self.data_entry_widget: DataEntryWidget | None = None

        self.name_layout = QHBoxLayout()
        self.init_ui(section_data)

    def init_ui(self, section_data):
        main_layout = QVBoxLayout()

        spacer_left  = QSpacerItem(80,  5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(300, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_layout.addItem(spacer_left)
        self.name_layout.addWidget(QLabel("Segment Name: "))
        self.segment_name_input = QLineEdit(self)
        self.segment_name_input.setFixedWidth(200)
        self.name_layout.addWidget(self.segment_name_input)
        self.name_layout.addItem(spacer_right)

        segment_label = QLabel("Segment Type:")
        segment_label.setFixedWidth(100)
        self.name_layout.addWidget(segment_label)
        self.segment_type_combo = QComboBox()
        self.segment_type_combo.addItems(self._SEGMENT_TYPES)
        self.segment_type_combo.setCurrentText("Segment")
        self.segment_type_combo.setFixedWidth(300)
        self.name_layout.addWidget(self.segment_type_combo, alignment=Qt.AlignmentFlag.AlignLeft)

        main_layout.addLayout(self.name_layout)

        data_units_labels = [
            ("Percent X Location", Units.Unitless),
            ("Percent Z Location", Units.Unitless),
            ("Height", Units.Length),
            ("Width", Units.Length),
        ]

        self.data_entry_widget = DataEntryWidget(data_units_labels)

        delete_button = QPushButton("Delete Section", self)
        delete_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        delete_button.setFixedWidth(150)
        delete_button.clicked.connect(self.delete_button_pressed)

        delete_button_layout = QHBoxLayout()
        delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        delete_button_layout.addWidget(delete_button)
        delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        main_layout.addWidget(self.data_entry_widget)
        main_layout.addLayout(delete_button_layout)

        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line_bar)

        if section_data:
            self.load_data_values(section_data)

        self.setLayout(main_layout)

    def create_rcaide_structure(self, data):
        selected = self.segment_type_combo.currentText()
        factory  = self._RCAIDE_SEGMENT_CLASS.get(selected, self._RCAIDE_SEGMENT_CLASS["Segment"])
        segment  = factory()
        segment.percent_x_location = data["Percent X Location"][0]
        segment.percent_z_location = data["Percent Z Location"][0]
        segment.height             = data["Height"][0]
        segment.width              = data["Width"][0]
        segment.tag                = data["Segment Name"]
        return segment

    def get_data_values(self):
        data    = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        name     = self.segment_name_input.text()
        seg_type = self.segment_type_combo.currentText()
        data["Segment Name"]    = name
        data["segment_type"]    = seg_type
        data_si["Segment Name"] = name
        data_si["segment_type"] = seg_type
        segment = self.create_rcaide_structure(data_si)
        return data, segment

    def load_data_values(self, data):
        self.data_entry_widget.load_data(data)
        self.segment_name_input.setText(data.get("Segment Name", ""))
        seg_type = data.get("segment_type", "Segment")
        idx = self.segment_type_combo.findText(seg_type)
        if idx >= 0:
            self.segment_type_combo.setCurrentIndex(idx)

    def delete_button_pressed(self):
        if self.on_delete is None:
            print("on_delete is None")
            return
        self.on_delete(self.index)
