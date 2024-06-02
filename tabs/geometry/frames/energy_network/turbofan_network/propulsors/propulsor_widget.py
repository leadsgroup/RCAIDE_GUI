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
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
            ("Inlet Nozzle", Units.Heading),
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
            ("Low Pressure Compressor", Units.Heading),
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
            ("High Pressure Compressor", Units.Heading),
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
            ("Core Nozzle", Units.Heading),
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
            ("Fan Nozzle", Units.Heading),
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
            ("Combustor", Units.Heading),
            ("Efficiency", Units.Unitless),
            ("Pressure Loss Coeff", Units.Unitless),
            ("Turbine Inlet Temp", Units.Temperature),
            ("Pressure Ratio", Units.Unitless),
        ]
        
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

    def load_data_values(self, section_data):
        data_values = section_data["data values"]
        self.data_entry_widget.load_data_values(data_values)        
        self.section_name_edit.setText(section_data["propulsor name"])

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
