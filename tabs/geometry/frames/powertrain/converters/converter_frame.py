# RCAIDE_GUI/tabs/geometry/frames/powertrain/converters/converter_frame.py
#
# Created:  Dec 2025, M. Clarke

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, \
    QSizePolicy, QSpacerItem

from tabs.geometry.widgets.powertrain.converters import TurboelectricGeneratorWidget
from common_widgets import DataEntryWidget

from utilities import BTN_STYLE

class ConverterFrame(QWidget):
    """Frame that manages a list of converter widgets (currently Turboelectric Generator).

    Converters sit between energy sources and propulsors — e.g. a turboelectric
    generator extracts shaft power from a gas turbine and feeds an electrical bus.
    """

    def __init__(self):
        super(ConverterFrame, self).__init__()

        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        # List to store data values source_ sections
        self.converter_sections_layout = QVBoxLayout()

        header_layout = QVBoxLayout()

        layout = self.create_scroll_layout()

        # Add source_ Section Button
        add_turboelectric_generator_button = QPushButton("Add Turboelectric Generator", self)
        add_turboelectric_generator_button.setStyleSheet(BTN_STYLE)
        add_turboelectric_generator_button.setMaximumWidth(200)
        add_turboelectric_generator_button.clicked.connect(self.add_turboelectric_generator) 
        header_layout.addWidget(add_turboelectric_generator_button)

        layout.addLayout(header_layout)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_bar)

        layout.addLayout(self.converter_sections_layout)

        button_layout = QHBoxLayout()

        layout.addLayout(button_layout)

        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def get_data_values(self):
        data = []
        sources = []
        for index in range(self.converter_sections_layout.count()):
            item = self.converter_sections_layout.itemAt(index)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, TurboelectricGeneratorWidget)

            source_data, fuel_tank = widget.get_data_values()
            data.append(source_data)
            sources.append(fuel_tank)

        return data, sources

    def load_data(self, data):
        while self.converter_sections_layout.count():
            widget_item = self.converter_sections_layout.itemAt(0)
            assert widget_item is not None
            widget = widget_item.widget()
            assert widget is not None

            self.converter_sections_layout.removeWidget(widget)
            widget.deleteLater()

        for section_data in data:
            self.converter_sections_layout.addWidget(TurboelectricGeneratorWidget(
                self.converter_sections_layout.count(), self.on_delete_button_pressed, section_data))

    def delete_data(self):
        pass

    def add_turboelectric_generator(self):
        self.converter_sections_layout.addWidget(
            TurboelectricGeneratorWidget(self.converter_sections_layout.count(), self.on_delete_button_pressed))

    def on_delete_button_pressed(self, index):
        distributor = self.converter_sections_layout.itemAt(index)
        if distributor is None:
            return

        widget = distributor.widget()
        if widget is None:
            return

        widget.deleteLater()
        self.converter_sections_layout.removeWidget(widget)
        self.converter_sections_layout.update() 

        for i in range(index, self.converter_sections_layout.count()):
            distributor = self.converter_sections_layout.itemAt(i)
            if distributor is None:
                continue

            widget = distributor.widget()
            if widget is None or not isinstance(widget, TurboelectricGeneratorWidget):
                continue

            widget.index = i 

    def set_save_function(self, function):
        self.save_function = function

    def create_scroll_layout(self):
        scroll_content = QWidget()
        
        layout = QVBoxLayout(scroll_content)

        self.setLayout(layout)

        return layout
