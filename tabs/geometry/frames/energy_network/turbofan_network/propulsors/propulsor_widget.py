from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox

from utilities import Units
from widgets.data_entry_widget import DataEntryWidget


class PropulsorWidget(QWidget):
    def __init__(self, index, on_delete, data_values=None):
        """Create a frame for entering landing gear data."""
        super(PropulsorWidget, self).__init__()

        # TODO: Add copying turbofan function (setting to new origin with same attributes)

        self.data_values = {}
        self.index = index
        self.on_delete = on_delete
        self.data_entry_widgets = []

        main_section_layout = QVBoxLayout()

        # Adding turbofan attributes
        turbofan_units_labels = [
            ("Origin", Units.Position),
            ("Engine Length", Units.Length),
            ("Bypass Ratio", Units.Unitless),
            ("Design Altitude", Units.Length),
            ("Design Mach Number", Units.Unitless),
            ("Design Thrust", Units.Force),
        ]

        self.name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        self.name_layout.addWidget(QLabel("Turbofan Name: "))
        self.name_layout.addWidget(self.section_name_edit)
        main_section_layout.addLayout(self.name_layout)

        # Adding turbofan label
        main_section_layout.addSpacing(8)
        turbofan_label = QLabel("Turbofan")
        font = turbofan_label.font()
        font.setBold(True)
        font.setUnderline(True)
        turbofan_label.setFont(font)
        main_section_layout.addWidget(turbofan_label)

        self.data_entry_widgets.append(DataEntryWidget(turbofan_units_labels))
        main_section_layout.addWidget(self.data_entry_widgets[-1])

        # Adding fan label
        main_section_layout.addSpacing(8)
        fan_layout = QVBoxLayout()
        fan_label = QLabel("Fan")
        font = fan_label.font()
        font.setBold(True)
        font.setUnderline(True)
        fan_label.setFont(font)
        fan_layout.addWidget(fan_label)
        main_section_layout.addLayout(fan_layout)

        fan_units_labels = [
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
        ]

        self.data_entry_widgets.append(DataEntryWidget(fan_units_labels))
        main_section_layout.addWidget(self.data_entry_widgets[-1])

        # Adding inlet nozzle label
        main_section_layout.addSpacing(8)
        inlet_nozzle_layout = QVBoxLayout()
        inlet_nozzle_label = QLabel("Inlet Nozzle")
        font = inlet_nozzle_label.font()
        font.setBold(True)
        font.setUnderline(True)
        inlet_nozzle_label.setFont(font)
        inlet_nozzle_layout.addWidget(inlet_nozzle_label)
        main_section_layout.addLayout(inlet_nozzle_layout)

        inlet_nozzle_units_labels = [
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
        ]

        self.data_entry_widgets.append(DataEntryWidget(inlet_nozzle_units_labels))
        main_section_layout.addWidget(self.data_entry_widgets[-1])

        # Adding low pressure compressor (lpc) label
        main_section_layout.addSpacing(8)
        lpc_layout = QVBoxLayout()
        lpc_label = QLabel("Low Pressure Compressor")
        font = lpc_label.font()
        font.setBold(True)
        font.setUnderline(True)
        lpc_label.setFont(font)
        lpc_layout.addWidget(lpc_label)
        main_section_layout.addLayout(lpc_layout)

        lpc_units_labels = [
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
        ]

        self.data_entry_widgets.append(DataEntryWidget(lpc_units_labels))
        main_section_layout.addWidget(self.data_entry_widgets[-1])

        # Adding high pressure compressor (hpc) label
        main_section_layout.addSpacing(8)
        hpc_layout = QVBoxLayout()
        hpc_label = QLabel("High Pressure Compressor")
        font = hpc_label.font()
        font.setBold(True)
        font.setUnderline(True)
        hpc_label.setFont(font)
        hpc_layout.addWidget(hpc_label)
        main_section_layout.addLayout(hpc_layout)

        hpc_units_labels = [
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
        ]

        self.data_entry_widgets.append(DataEntryWidget(hpc_units_labels))
        main_section_layout.addWidget(self.data_entry_widgets[-1])

        # Adding core nozzle label
        main_section_layout.addSpacing(8)
        core_nozzle_layout = QVBoxLayout()
        core_nozzle_label = QLabel("Core Nozzle")
        font = core_nozzle_label.font()
        font.setBold(True)
        font.setUnderline(True)
        core_nozzle_label.setFont(font)
        core_nozzle_layout.addWidget(core_nozzle_label)
        main_section_layout.addLayout(core_nozzle_layout)

        core_nozzle_units_labels = [
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
        ]

        self.data_entry_widgets.append(DataEntryWidget(core_nozzle_units_labels))
        main_section_layout.addWidget(self.data_entry_widgets[-1])

        # Adding fan nozzle label
        main_section_layout.addSpacing(8)
        fan_nozzle_layout = QVBoxLayout()
        fan_nozzle_label = QLabel("Fan Nozzle")
        font = fan_nozzle_label.font()
        font.setBold(True)
        font.setUnderline(True)
        fan_nozzle_label.setFont(font)
        fan_nozzle_layout.addWidget(fan_nozzle_label)
        main_section_layout.addLayout(fan_nozzle_layout)

        fan_nozzle_units_labels = [
            ("Polytropic Efficiency", Units.Unitless),
            ("Pressure Ratio", Units.Unitless),
        ]

        self.data_entry_widgets.append(DataEntryWidget(fan_nozzle_units_labels))
        main_section_layout.addWidget(self.data_entry_widgets[-1])

        # Adding combustor label
        main_section_layout.addSpacing(8)
        combustor_layout = QVBoxLayout()
        combustor_label = QLabel("Combustor")
        font = combustor_label.font()
        font.setBold(True)
        font.setUnderline(True)
        combustor_label.setFont(font)
        combustor_layout.addWidget(combustor_label)
        main_section_layout.addLayout(combustor_layout)

        combustor_units_labels = [
            ("Efficiency", Units.Unitless),
            ("Pressure Loss Coeff", Units.Unitless),
            ("Turbine Inlet Temp", Units.Temperature),
            ("Pressure Ratio", Units.Unitless),
        ]

        self.data_entry_widgets.append(DataEntryWidget(combustor_units_labels))
        main_section_layout.addWidget(self.data_entry_widgets[-1])

        # # Adding option to deepcopy turbofan
        # main_section_layout.addSpacing(8)
        # copy_layout = QVBoxLayout()
        # copy_label = QLabel("Copy Turbofan?")
        # font = copy_label.font()
        # font.setBold(True)
        # font.setUnderline(True)
        # copy_label.setFont(font)
        # copy_layout.addWidget(copy_label)
        # main_section_layout.addLayout(copy_layout)
        
        # # TODO: Change to duplicate turbofan
        # # TODO: Make sure 2 turbofans aren't at the same origin
        
        # self.copy_turbofan_checkbox = QCheckBox("Yes, copy turbofan properties to new origin")
        # self.copy_turbofan_checkbox.setChecked(False)
        # main_section_layout.addWidget(self.copy_turbofan_checkbox)

        # # Deepcopy turbofan labels and units
        # deepcopy_units_labels = [
        #     ("New Origin", Units.Length),
        # ]

        # self.data_entry_widget = DataEntryWidget(deepcopy_units_labels)
        # self.data_entry_widget.setVisible(False)
        # main_section_layout.addWidget(self.data_entry_widget)
        # self.copy_turbofan_checkbox.stateChanged.connect(self.toggle_deepcopy_visibility)

        # Adding delete button
        delete_button = QPushButton("Delete Propulsor", self)
        delete_button.clicked.connect(self.delete_button_pressed)
        
        #TODO : Add separator

        main_section_layout.addWidget(delete_button)

        self.setLayout(main_section_layout)

        if data_values:
            self.load_data_values(data_values)

    def load_data_values(self, section_data):
        for i, data in enumerate(section_data["data values"]):
            self.data_entry_widgets[i].load_data(data)
        
        self.section_name_edit.setText(section_data["propulsor name"])

    def delete_button_pressed(self):
        print("Delete button pressed")

        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)

    def get_data_values(self):
        title = self.section_name_edit.text()
        data = {}
        data_values = []
        for widget in self.data_entry_widgets:
            assert isinstance(widget, DataEntryWidget)
            data_values.append(widget.get_values())
            
        data["propulsor name"] = title
        data["data values"] = data_values
        return data
