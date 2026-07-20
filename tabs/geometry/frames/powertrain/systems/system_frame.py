# RCAIDE_GUI/tabs/geometry/frames/powertrain/systems/system_frame.py
#
# Created:  Jun 2026, M. Clarke

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QFrame, QSizePolicy, QSpacerItem, QComboBox)

from tabs.geometry.widgets.powertrain.systems import SystemWidget

from utilities import BTN_STYLE

_SYSTEM_TYPES = [
    "Avionics",
    "Auxiliary Power Unit",
    "Cabin Loads",
    "Electrical",
    "Environmental Controls",
    "Flight Controls",
    "Furnishings",
    "Hydraulics",
    "Ice Protection",
    "Instruments",
    "Water Tank",
]

class SystemFrame(QWidget):
    """Frame that manages a list of system widgets.

    A type dropdown lets the user choose which system kind to add before
    clicking the Add button, mirroring the pattern used by PropulsorFrame
    and DistributorFrame.
    """

    def __init__(self):
        super().__init__()

        self.systems_layout = QVBoxLayout()

        layout = self._create_scroll_layout()

        add_layout = QHBoxLayout()
        self.system_type_dropdown = QComboBox(self)
        self.system_type_dropdown.addItems(_SYSTEM_TYPES)
        self.system_type_dropdown.setMinimumWidth(220)
        self.system_type_dropdown.currentTextChanged.connect(self._update_add_button_text)
        add_layout.addWidget(self.system_type_dropdown)

        self.add_system_button = QPushButton(f"Add {_SYSTEM_TYPES[0]}", self)
        self.add_system_button.setStyleSheet(BTN_STYLE)
        self.add_system_button.setMinimumWidth(220)
        self.add_system_button.setMaximumWidth(280)
        self.add_system_button.clicked.connect(self.add_system)
        add_layout.addWidget(self.add_system_button)
        add_layout.addStretch()
        layout.addLayout(add_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: light grey;")
        layout.addWidget(line)

        layout.addLayout(self.systems_layout)
        layout.addLayout(QHBoxLayout())
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding,
                                   QSizePolicy.Policy.Expanding))

    def _update_add_button_text(self, system_type):
        self.add_system_button.setText(f"Add {system_type}")

    def add_system(self):
        sys_type = self.system_type_dropdown.currentText()
        self.systems_layout.addWidget(
            SystemWidget(self.systems_layout.count(), self._on_delete,
                         {"System Type": sys_type}))

    def _on_delete(self, index):
        item = self.systems_layout.itemAt(index)
        if item is None:
            return
        widget = item.widget()
        if widget is None:
            return
        widget.deleteLater()
        self.systems_layout.removeWidget(widget)
        self.systems_layout.update()
        for i in range(index, self.systems_layout.count()):
            w = self.systems_layout.itemAt(i)
            if w and isinstance(w.widget(), SystemWidget):
                w.widget().index = i

    def get_data_values(self):
        data = []
        systems = []
        for i in range(self.systems_layout.count()):
            item = self.systems_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if not isinstance(widget, SystemWidget):
                continue
            sys_data, sys_obj = widget.get_data_values()
            data.append(sys_data)
            systems.append(sys_obj)
        return data, systems

    def load_data(self, data):
        while self.systems_layout.count():
            item = self.systems_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        for sys_data in data:
            w = SystemWidget(self.systems_layout.count(), self._on_delete, sys_data)
            self.systems_layout.addWidget(w)

    def _create_scroll_layout(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        self.setLayout(layout)
        return layout
