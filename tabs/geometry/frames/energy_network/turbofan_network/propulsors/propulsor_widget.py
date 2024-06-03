from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame

from utilities import Units
from widgets.data_entry_widget import DataEntryWidget


class PropulsorWidget(QWidget):
    def __init__(self, index, on_delete, data_values=None):
        """Create a frame for entering landing gear data."""
        super(PropulsorWidget, self).__init__()

        self.data_values = {}
        self.index = index
        self.on_delete = on_delete

        main_section_layout = QVBoxLayout()
        
        # TODO: Change to duplicate turbofan
        # TODO: Make sure 2 turbofans aren't at the same origin
    
        data_units_labels = [
            ("Turbofan", Units.Heading),
            ("Origin", Units.Position),
            ("Engine Length", Units.Length),
            ("Bypass Ratio", Units.Unitless),
            ("Design Altitude", Units.Length),
            ("Design Mach Number", Units.Unitless),
            ("Design Thrust", Units.Force),            
            ("Fan", Units.Heading),
            ("Fan Polytropic Efficiency", Units.Unitless),
            ("Fan Pressure Ratio", Units.Unitless),
            ("Inlet Nozzle", Units.Heading),
            ("IN Polytropic Efficiency", Units.Unitless),
            ("IN Pressure Ratio", Units.Unitless),
            ("Low Pressure Compressor", Units.Heading),
            ("LPC Polytropic Efficiency", Units.Unitless),
            ("LPC Pressure Ratio", Units.Unitless),
            ("High Pressure Compressor", Units.Heading),
            ("HPC Polytropic Efficiency", Units.Unitless),
            ("HPC Pressure Ratio", Units.Unitless),
            ("Core Nozzle", Units.Heading),
            ("CN Polytropic Efficiency", Units.Unitless),
            ("CN Pressure Ratio", Units.Unitless),
            ("Fan Nozzle", Units.Heading),
            ("FN Polytropic Efficiency", Units.Unitless),
            ("FN Pressure Ratio", Units.Unitless),
            ("Combustor", Units.Heading),
            ("Combustor Efficiency", Units.Unitless),
            ("Combustor Pressure Loss Coeff", Units.Unitless),
            ("Combustor Turbine Inlet Temp", Units.Temperature),
            ("Combustor Pressure Ratio", Units.Unitless),
        ]

        self.name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        self.name_layout.addWidget(QLabel("Turbofan Name: "))
        self.name_layout.addWidget(self.section_name_edit)
        main_section_layout.addLayout(self.name_layout)
        
        self.data_entry_widget = DataEntryWidget(data_units_labels)
        main_section_layout.addWidget(self.data_entry_widget)

        # Adding delete button
        delete_button = QPushButton("Delete Propulsor", self)
        delete_button.clicked.connect(self.delete_button_pressed)

        main_section_layout.addWidget(delete_button)
        
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")
        
        main_section_layout.addWidget(line_bar)

        self.setLayout(main_section_layout)

        if data_values:
            self.load_data_values(data_values)

    def load_data_values(self, data):
        self.data_entry_widget.load_data(data)        
        self.section_name_edit.setText(data["propulsor name"])

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)

    def get_data_values(self):
        title = self.section_name_edit.text()
        data = self.data_entry_widget.get_values()
        data["propulsor name"] = title
        return data
