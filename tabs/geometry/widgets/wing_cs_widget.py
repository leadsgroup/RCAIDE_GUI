import RCAIDE
from PyQt6.QtWidgets import (QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget, QFrame, QComboBox)

from utilities import Units
from widgets import DataEntryWidget

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
        ("Number of Slots", Units.Count),
    ],
]
cs_types = ["Aileron", "Slat", "Flap"]


class WingCSWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None):
        super(WingCSWidget, self).__init__()

        # self.data_fields = {}
        self.coordinate_filename = ""
        self.index = index
        self.on_delete = on_delete
        self.data_entry_widget: DataEntryWidget | None = None
        self.main_layout: QVBoxLayout | None = None
        self.cs_type = 0

        self.name_layout = QHBoxLayout()
        self.init_ui(section_data)

    # noinspection DuplicatedCode
    def init_ui(self, section_data):
        self.main_layout = QVBoxLayout()
        # add spacing
        spacer_left = QSpacerItem(80, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(300, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_layout.addItem(spacer_left)
        self.name_layout.addWidget(QLabel("Control Surface Name: "))
        self.name_layout.addWidget(QLineEdit(self))

        cs_type_dropdown = QComboBox()
        cs_type_dropdown.addItems(cs_types)
        cs_type_dropdown.setFixedWidth(100)
        cs_type_dropdown.currentIndexChanged.connect(self.on_dropdown_change)
        self.name_layout.addWidget(cs_type_dropdown)
        self.name_layout.addItem(spacer_right)

        self.main_layout.addLayout(self.name_layout)

        self.data_entry_widget = DataEntryWidget(data_units_labels[0])
        self.main_layout.addWidget(self.data_entry_widget)

        # Delete button layout
        delete_button = QPushButton("Delete Control Surface")
        delete_button.clicked.connect(self.delete_button_pressed)
        delete_button_layout = QHBoxLayout()
        delete_button_layout.addWidget(delete_button)
        delete_button_layout.setSpacing(0)
        self.main_layout.addLayout(delete_button_layout)

        # Add horizontal bar
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line_bar)

        if section_data:
            self.load_data_values(section_data)

        self.setLayout(self.main_layout)

    def on_dropdown_change(self, index):
        """Change the index of the main layout based on the selected index of the dropdown.

        Args:
            index: The index of the selected item in the dropdown.
        """
        self.main_layout.removeWidget(self.data_entry_widget)
        self.data_entry_widget.deleteLater()
        self.data_entry_widget = DataEntryWidget(data_units_labels[index])
        self.main_layout.insertWidget(1, self.data_entry_widget)
        self.cs_type = index

    def create_rcaide_structure(self, data):
        cs = None
        if self.cs_type == 0:
            cs = RCAIDE.Library.Components.Wings.Control_Surfaces.Aileron()
        elif self.cs_type == 1:
            cs = RCAIDE.Library.Components.Wings.Control_Surfaces.Slat()
        elif self.cs_type == 2:
            cs = RCAIDE.Library.Components.Wings.Control_Surfaces.Flap()

        cs.tag = data["CS name"]
        cs.span_fraction_start = data["Span Fraction Start"][0]
        cs.span_fraction_end = data["Span Fraction End"][0]
        cs.deflection = data["Deflection"][0]
        cs.chord_fraction = data["Chord Fraction"][0]

        if self.cs_type == 2:
            num_slots = data["Number of Slots"][0]
            config_type = "single_slotted"
            if num_slots == 2:
                config_type = "double_slotted"
            elif num_slots == 3:
                config_type = "triple_slotted"
            elif num_slots != 1:
                print("Illegal number of slots. Defaulting to single slotted.")

            cs.configuration_type = config_type

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
