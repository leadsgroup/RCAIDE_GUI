# RCAIDE_GUI/tabs/geometry/frames/powertrain/converters/converter_frame.py
#
# Created:  Dec 2025, M. Clarke

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
                              QSizePolicy, QSpacerItem, QComboBox)

from tabs.geometry.widgets.powertrain.converters import TurboelectricGeneratorWidget

from utilities import BTN_STYLE

_CONVERTER_TYPES = [
    "Turboelectric Generator",
]

_CONVERTER_WIDGETS = {
    "Turboelectric Generator": TurboelectricGeneratorWidget,
}


class ConverterFrame(QWidget):
    """Frame that manages a list of converter widgets.

    A type dropdown lets the user choose which converter kind to add.
    Currently only Turboelectric Generator is implemented.
    """

    def __init__(self):
        super(ConverterFrame, self).__init__()

        self.converter_sections_layout = QVBoxLayout()

        layout = self.create_scroll_layout()

        add_layout = QHBoxLayout()
        self.converter_type_dropdown = QComboBox(self)
        self.converter_type_dropdown.addItems(_CONVERTER_TYPES)
        self.converter_type_dropdown.setMinimumWidth(220)
        self.converter_type_dropdown.currentTextChanged.connect(self._update_add_button_text)
        add_layout.addWidget(self.converter_type_dropdown)

        self.add_converter_button = QPushButton(f"Add {_CONVERTER_TYPES[0]}", self)
        self.add_converter_button.setStyleSheet(BTN_STYLE)
        self.add_converter_button.setMinimumWidth(220)
        self.add_converter_button.setMaximumWidth(280)
        self.add_converter_button.clicked.connect(self.add_selected_converter)
        add_layout.addWidget(self.add_converter_button)
        add_layout.addStretch()
        layout.addLayout(add_layout)

        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")
        layout.addWidget(line_bar)

        layout.addLayout(self.converter_sections_layout)
        layout.addLayout(QHBoxLayout())
        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def _update_add_button_text(self, converter_type):
        self.add_converter_button.setText(f"Add {converter_type}")

    def add_selected_converter(self):
        converter_type = self.converter_type_dropdown.currentText()
        cls = _CONVERTER_WIDGETS.get(converter_type, TurboelectricGeneratorWidget)
        self.converter_sections_layout.addWidget(
            cls(self.converter_sections_layout.count(), self.on_delete_button_pressed))

    def get_data_values(self):
        data = []
        converters = []
        for index in range(self.converter_sections_layout.count()):
            item = self.converter_sections_layout.itemAt(index)
            if item is None:
                continue
            widget = item.widget()
            if not isinstance(widget, TurboelectricGeneratorWidget):
                continue
            conv_data, conv_obj = widget.get_data_values()
            data.append(conv_data)
            converters.append(conv_obj)
        return data, converters

    def load_data(self, data):
        while self.converter_sections_layout.count():
            item = self.converter_sections_layout.itemAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is None:
                break
            self.converter_sections_layout.removeWidget(widget)
            widget.deleteLater()

        for section_data in data:
            self.converter_sections_layout.addWidget(TurboelectricGeneratorWidget(
                self.converter_sections_layout.count(), self.on_delete_button_pressed, section_data))

    def delete_data(self):
        pass

    def on_delete_button_pressed(self, index):
        item = self.converter_sections_layout.itemAt(index)
        if item is None:
            return
        widget = item.widget()
        if widget is None:
            return
        widget.deleteLater()
        self.converter_sections_layout.removeWidget(widget)
        self.converter_sections_layout.update()

        for i in range(index, self.converter_sections_layout.count()):
            item = self.converter_sections_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None and isinstance(widget, TurboelectricGeneratorWidget):
                widget.index = i

    def set_save_function(self, function):
        self.save_function = function

    def create_scroll_layout(self):
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        self.setLayout(layout)
        return layout
