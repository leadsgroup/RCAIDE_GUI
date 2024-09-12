import RCAIDE
from PyQt6.QtWidgets import (QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget, QFrame)

from utilities import Units
from widgets import DataEntryWidget


class WingSectionWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None):
        super(WingSectionWidget, self).__init__()

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
            # ("Airfoil", Units.Unitless),
        ]

        self.data_entry_widget = DataEntryWidget(data_units_labels)

        # Delete button
        delete_button = QPushButton("Delete Wing Segment", self)
        # delete_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # delete_button.setFixedWidth(150)
        delete_button.clicked.connect(self.delete_button_pressed)

        # Center delete button
        delete_button_layout = QHBoxLayout()
        # delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        delete_button_layout.addWidget(delete_button)
        # delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

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
        segment = RCAIDE.Library.Components.Wings.Segment()

        segment.tag = data["segment name"]
        segment.percent_span_location = data["Percent Span Location"][0]
        segment.twist = data["Twist"][0]

        segment.root_chord_percent = data["Root Chord Percent"][0]
        segment.thickness_to_chord = data["Thickness to Chord"][0]
        segment.dihedral_outboard = data["Dihedral Outboard"][0]
        segment.sweeps.quarter_chord = data["Quarter Chord Sweep"][0]
        # segment.airfoil = data["Airfoil"][0]

        return segment

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data_si["segment name"] = self.name_layout.itemAt(2).widget().text()

        wing_section = self.create_rcaide_structure(data_si)
        data["segment name"] = self.name_layout.itemAt(2).widget().text()
        return data, wing_section

    def load_data_values(self, section_data):
        self.data_entry_widget.load_data(section_data)
        self.name_layout.itemAt(2).widget().setText(section_data["segment name"])

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)
