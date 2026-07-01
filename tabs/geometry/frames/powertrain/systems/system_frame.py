# RCAIDE_GUI/tabs/geometry/frames/powertrain/systems/system_frame.py
#
# Created:  Jun 2026, M. Clarke

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QFrame, QSizePolicy, QSpacerItem)

from tabs.geometry.widgets.powertrain.systems import SystemWidget


class SystemFrame(QWidget):
    def __init__(self):
        super().__init__()

        self.systems_layout = QVBoxLayout()

        layout = self._create_scroll_layout()

        header_layout = QVBoxLayout()
        add_btn = QPushButton("Add System", self)
        add_btn.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        add_btn.setMaximumWidth(200)
        add_btn.clicked.connect(self.add_system)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: light grey;")
        layout.addWidget(line)

        layout.addLayout(self.systems_layout)
        layout.addLayout(QHBoxLayout())
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding,
                                   QSizePolicy.Policy.Expanding))

    def add_system(self):
        self.systems_layout.addWidget(
            SystemWidget(self.systems_layout.count(), self._on_delete))

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
