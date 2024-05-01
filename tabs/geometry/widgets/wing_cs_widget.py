import RCAIDE
from PyQt6.QtWidgets import (QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget, QFrame)

from utilities import Units
from widgets.data_entry_widget import DataEntryWidget


class WingCSWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None):
        super(WingCSWidget, self).__init__()

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
        self.name_layout.addWidget(QLabel("Control Surface Name: "))
        self.name_layout.addWidget(QLineEdit(self))
        self.name_layout.addItem(spacer_right)

        main_layout.addLayout(self.name_layout)

        # Delete button layout
        delete_button = QPushButton("Delete Control Surface")
        delete_button.clicked.connect(self.delete_button_pressed)
        delete_button_layout = QHBoxLayout()
        delete_button_layout.addWidget(delete_button)
        delete_button_layout.setSpacing(0)
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
        cs = RCAIDE.Library.Components.Wings.Control_Surfaces.Control_Surface()
        cs.tag = data["CS name"]

        return cs

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data["CS name"] = self.name_layout.itemAt(2).widget().text()
        data_si["CS name"] = self.name_layout.itemAt(2).widget().text()

        cs = self.create_rcaide_structure(data_si)
        return data, cs

    def load_data_values(self, section_data):
        self.data_entry_widget.load_data(section_data)
        self.name_layout.itemAt(2).widget().setText(section_data["CS name"])

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)


data_units_labels = [
    [
        ("Span Fraction Start", Units.Unitless),
        ("Span Fraction End", Units.Unitless),
        ("Deflection", Units.Angle),
        ("Chord Fraction", Units.Unitless),
    ],
    [
        ("Span Fraction Start", Units.Unitless),
        ("Span Fraction End", Units.Unitless),
        ("Deflection", Units.Angle),
        ("Chord Fraction", Units.Unitless),
    ],
    [
        ("Span Fraction Start", Units.Unitless),
        ("Span Fraction End", Units.Unitless),
        ("Deflection", Units.Angle),
        ("Chord Fraction", Units.Unitless),
        ("Configuration", Units.Unitless),
    ],
]
