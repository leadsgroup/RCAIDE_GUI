# RCAIDE_GUI/tabs/geometry/frames/powertrain/propulsors/propulsor_frame.py
# 
# Created:  Dec 2025, M. Clarke 

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
# RCAIDE imports   
import RCAIDE

# PyQT Imports
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QFrame, QComboBox

# RCAIDE GUI imports  
from tabs.geometry.widgets.powertrain.propulsors.turbofan_widget import TurbofanWidget
from tabs.geometry.widgets.powertrain.propulsors.base_propulsor_widget import BasePropulsorWidget
from tabs.geometry.widgets.powertrain.propulsors.constant_speed_ice_widget import ConstantSpeedICEWidget
from tabs.geometry.widgets.powertrain.propulsors.electric_ducted_fan_widget import ElectricDuctedFanWidget
from tabs.geometry.widgets.powertrain.propulsors.electric_rotor_widget import ElectricRotorWidget
from tabs.geometry.widgets.powertrain.propulsors.ice_widget import ICEWidget
from tabs.geometry.widgets.powertrain.propulsors.turbojet_widget import TurbojetWidget
from tabs.geometry.widgets.powertrain.propulsors.turboprop_widget import TurbopropWidget
from common_widgets import DataEntryWidget
from utilities import show_popup, create_line_bar, set_data, Units, create_scroll_area, clear_layout, BTN_STYLE
import rcaide_io

# Non-turbofan propulsors are selected by display name and constructed here.
PROPULSOR_WIDGETS = {
    "Constant Speed Internal Combustion Engine": ConstantSpeedICEWidget,
    "Electric Ducted Fan": ElectricDuctedFanWidget,
    "Electric Rotor": ElectricRotorWidget,
    "Internal Combustion Engine": ICEWidget,
    "Turbojet": TurbojetWidget,
    "Turboprop": TurbopropWidget,
}

# --------------------------------------------------------------------------------------------------------------------- 
#  Propulsor Frame 
# ----------------------------------------------------------------------------------------------------------------------
class PropulsorFrame(QWidget):
    """Frame that manages a list of propulsor widgets of any type.

    A type dropdown (populated from ``PROPULSOR_WIDGETS`` plus "Turbofan")
    controls which widget class is instantiated when the user clicks "Add".
    ``load_data()`` detects the saved type via ``"Propulsor Type"`` or,
    for legacy files, from ``"__type__"`` — see ``_propulsor_type_from_data()``.

    Supported types: Turbofan, Turbojet, Turboprop, Electric Rotor,
    Electric Ducted Fan, Internal Combustion Engine, Constant Speed ICE.
    """

    def __init__(self):
        super(PropulsorFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        self.propulsor_sections_layout = QVBoxLayout()

        header_layout = QVBoxLayout()

        layout = self.create_scroll_layout()

        # Let the user choose which propulsor widget to add instead of always
        # creating a turbofan section.
        add_layout = QHBoxLayout()
        self.propulsor_type_dropdown = QComboBox(self)
        self.propulsor_type_dropdown.addItems(sorted([
            "Constant Speed Internal Combustion Engine",
            "Electric Ducted Fan",
            "Electric Rotor",
            "Internal Combustion Engine",
            "Turbofan",
            "Turbojet",
            "Turboprop",
        ]))
        self.propulsor_type_dropdown.setMinimumWidth(390)
        self.propulsor_type_dropdown.currentTextChanged.connect(self.update_add_button_text)
        add_layout.addWidget(self.propulsor_type_dropdown)

        # Keep the action label synced with the dropdown selection.
        self.add_propulsor_button = QPushButton(
            f"Add {self.propulsor_type_dropdown.currentText()}",
            self,
        )
        self.add_propulsor_button.setStyleSheet(BTN_STYLE)
        self.add_propulsor_button.setMinimumWidth(430)
        self.add_propulsor_button.setMaximumWidth(480)
        self.add_propulsor_button.clicked.connect(self.add_selected_propulsor)
        add_layout.addWidget(self.add_propulsor_button)
        add_layout.addStretch()
        header_layout.addLayout(add_layout)

        layout.addLayout(header_layout)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_bar)

        layout.addLayout(self.propulsor_sections_layout)

        button_layout = QHBoxLayout()

        layout.addLayout(button_layout)

        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def get_data_values(self):
        """Retrieve the entered data values from the dictionary for the propulsor sections."""

        # Collect data from additional fuselage_widget
        data = []
        propulsors = []
        rcaide_io.propulsor_names = [[]]
        for index in range(self.propulsor_sections_layout.count()):
            item = self.propulsor_sections_layout.itemAt(index)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, (TurbofanWidget, BasePropulsorWidget))

            propulsor_data, propulsor = widget.get_data_values()
            data.append(propulsor_data)
            propulsors.append(propulsor)

        return data, propulsors

    def load_data(self, data):
        while self.propulsor_sections_layout.count():
            item = self.propulsor_sections_layout.takeAt(0)
            assert item is not None
            widget = item.widget()
            assert widget is not None

            self.propulsor_sections_layout.removeWidget(widget)
            widget.deleteLater()

        for propulsor_data in data:
            propulsor_type = self._propulsor_type_from_data(propulsor_data)
            self.propulsor_sections_layout.addWidget(
                self._new_propulsor_widget(propulsor_type, propulsor_data)
            )

    def delete_data(self):
        """Delete the entered data or perform any other action."""
        # TODO: Implement proper deletion of data

    def add_turbofan(self):
        self.propulsor_sections_layout.addWidget(
            TurbofanWidget(self.propulsor_sections_layout.count(), self.on_delete_button_pressed))

    def add_selected_propulsor(self):
        propulsor_type = self.propulsor_type_dropdown.currentText()
        self.propulsor_sections_layout.addWidget(self._new_propulsor_widget(propulsor_type))

    def update_add_button_text(self, propulsor_type):
        self.add_propulsor_button.setText(f"Add {propulsor_type}")

    def _new_propulsor_widget(self, propulsor_type, data_values=None):
        index = self.propulsor_sections_layout.count()
        if propulsor_type == "Turbofan":
            return TurbofanWidget(index, self.on_delete_button_pressed, data_values)
        # Named widget classes keep each non-turbofan propulsor in its own file.
        return PROPULSOR_WIDGETS[propulsor_type](index, self.on_delete_button_pressed, data_values)

    def _propulsor_type_from_data(self, data):
        propulsor_type = data.get("Propulsor Type", "")
        if propulsor_type == "Turbofan" or propulsor_type in PROPULSOR_WIDGETS:
            return propulsor_type

        # Older saved files may only have the RCAIDE class path instead of the GUI type.
        type_string = data.get("__type__", "")
        class_name = type_string.rsplit(".", 1)[-1]
        type_lookup = {
            "Constant_Speed_Internal_Combustion_Engine": "Constant Speed Internal Combustion Engine",
            "Electric_Ducted_Fan": "Electric Ducted Fan",
            "Electric_Rotor": "Electric Rotor",
            "Internal_Combustion_Engine": "Internal Combustion Engine",
            "Turbofan": "Turbofan",
            "Turbojet": "Turbojet",
            "Turboprop": "Turboprop",
        }
        return type_lookup.get(class_name, "Turbofan")

    def on_delete_button_pressed(self, index):
        propulsor = self.propulsor_sections_layout.itemAt(index)
        if propulsor is None:
            return

        widget = propulsor.widget()
        if widget is None:
            return

        widget.deleteLater()
        self.propulsor_sections_layout.removeWidget(widget)
        self.propulsor_sections_layout.update() 

        for i in range(index, self.propulsor_sections_layout.count()):
            propulsor = self.propulsor_sections_layout.itemAt(i)
            if propulsor is None:
                continue

            widget = propulsor.widget()
            if widget is None or not isinstance(widget, (TurbofanWidget, BasePropulsorWidget)):
                continue

            widget.index = i 

    def update_units(self, line_edit, unit_combobox):
        pass

    def create_scroll_layout(self):
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        self.setLayout(layout)

        return layout
