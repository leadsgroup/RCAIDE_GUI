# RCAIDE_GUI/tabs/geometry/frames/powertrain/sources/energy_source_frame.py
# 
# Created:  Dec 2025, M. Clarke 

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
# RCAIDE imports   
import RCAIDE

# PyQT Imports
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QScrollArea

# RCAIDE GUI imports  
from tabs.geometry.widgets.powertrain.propulsors.turbofan_widget import TurbofanWidget
from widgets import DataEntryWidget
from utilities import show_popup, create_line_bar, set_data, Units, create_scroll_area, clear_layout
import values

# --------------------------------------------------------------------------------------------------------------------- 
#  Propulsor Frame 
# ----------------------------------------------------------------------------------------------------------------------
class PropulsorFrame(QWidget):
    def __init__(self):
        super(PropulsorFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        # List to store data values propulsor_ sections
        self.propulsor_sections_layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QVBoxLayout()
        # label = QLabel("<u><b>Propulsor Frame</b></u>")

        layout = self.create_scroll_layout()

        # header_layout.addWidget(label)

        # Add propulsor_ Section Button
        add_turbofan_button = QPushButton("Add Turbofan", self)
        add_turbofan_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        add_turbofan_button.setMaximumWidth(200)
        add_turbofan_button.clicked.connect(self.add_turbofan)
        header_layout.addWidget(add_turbofan_button)

        layout.addLayout(header_layout)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Add the layout for additional propulsor_ sections to the main layout
        layout.addLayout(self.propulsor_sections_layout)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def get_data_values(self):
        """Retrieve the entered data values from the dictionary for the propulsor sections."""

        # Collect data from additional fuselage_widget
        data = []
        propulsors = []
        values.propulsor_names = [[]]
        for index in range(self.propulsor_sections_layout.count()):
            item = self.propulsor_sections_layout.itemAt(index)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, TurbofanWidget)

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
            self.propulsor_sections_layout.addWidget(TurbofanWidget(
                self.propulsor_sections_layout.count(), self.on_delete_button_pressed, propulsor_data))

    def delete_data(self):
        """Delete the entered data or perform any other action."""
        # TODO: Implement proper deletion of data

    def add_turbofan(self):
        self.propulsor_sections_layout.addWidget(
            TurbofanWidget(self.propulsor_sections_layout.count(), self.on_delete_button_pressed))

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
            if widget is None or not isinstance(widget, TurbofanWidget):
                continue

            widget.index = i 

    def update_units(self, line_edit, unit_combobox):
        pass

    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Set the main layout of the widget
        self.setLayout(layout)

        return layout
