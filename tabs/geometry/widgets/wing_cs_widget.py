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


        # Aileron labels and units
        aileron_units_labels = [
            ("Span Fraction Start", Units.Unitless),
            ("Span Fraction End", Units.Unitless),
            ("Deflection", Units.Angle),
            ("Chord Fraction", Units.Unitless),
        ]        
        
        main_layout.addSpacing(8)
        aileron_label = QLabel("Aileron")
        font = aileron_label.font()
        font.setBold(True)
        font.setUnderline(True)
        aileron_label.setFont(font)
        main_layout.addWidget(aileron_label)        

        self.data_entry_widget = DataEntryWidget(aileron_units_labels)
        main_layout.addWidget(self.data_entry_widget)   
        
        # Slat labels and units
        slat_units_labels = [
            ("Span Fraction Start", Units.Unitless),
            ("Span Fraction End", Units.Unitless),
            ("Deflection", Units.Angle),
            ("Chord Fraction", Units.Unitless),
        ]        
        
        main_layout.addSpacing(8)
        slat_label = QLabel("Slat")
        font = slat_label.font()
        font.setBold(True)
        font.setUnderline(True)
        slat_label.setFont(font)
        main_layout.addWidget(slat_label)        

        self.data_entry_widget = DataEntryWidget(slat_units_labels)
        main_layout.addWidget(self.data_entry_widget)        
        
        # Flap labels and units
        flap_units_labels = [
            ("Span Fraction Start", Units.Unitless),
            ("Span Fraction End", Units.Unitless),
            ("Deflection", Units.Angle),
            ("Chord Fraction", Units.Unitless),
            ("Configuration", Units.Unitless),
        ]        
        
        main_layout.addSpacing(8)
        flap_label = QLabel("Flap")
        font = slat_label.font()
        font.setBold(True)
        font.setUnderline(True)
        flap_label.setFont(font)
        main_layout.addWidget(flap_label)        

        self.data_entry_widget = DataEntryWidget(flap_units_labels)
        main_layout.addWidget(self.data_entry_widget)        
        

        # Delete button layout
        delete_button = QPushButton("Delete Control Surface")
        delete_button.clicked.connect(self.delete_button_pressed)
        delete_button_layout = QHBoxLayout()
        delete_button_layout.addWidget(delete_button)
        delete_button_layout.setSpacing(0)  # No spacing inside delete button layout
        main_layout.addLayout(delete_button_layout)
    
        # Add horizontal bar immediately below the delete button
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line_bar)

        if section_data:
            self.load_data_values(section_data)

        self.setLayout(main_layout)
   

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data["CS name"] = self.name_layout.itemAt(2).widget().text()
        return data

    def load_data_values(self, section_data):
        self.data_entry_widget.load_data(section_data)
        self.name_layout.itemAt(2).widget().setText(section_data["CS name"])

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)
