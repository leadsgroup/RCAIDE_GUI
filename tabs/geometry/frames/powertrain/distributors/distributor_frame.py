# RCAIDE_GUI/tabs/geometry/frames/powertrain/distributor_frame.py
#
# Created:  Dec 2025, M. Clarke

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------
from PyQt6.QtWidgets import (QWidget, QPushButton, QSizePolicy, QVBoxLayout,
                              QHBoxLayout, QFrame, QSpacerItem, QComboBox)

from tabs.geometry.widgets.powertrain.distributors.base_distributor_widget import BaseDistributorWidget
from tabs.geometry.widgets.powertrain.distributors.fuel_line_widget        import FuelLineWidget
from tabs.geometry.widgets.powertrain.distributors.electrical_bus_widget   import ElectricalBusWidget
from tabs.geometry.widgets.powertrain.distributors.coolant_line_widget     import CoolantLineWidget
from common_widgets import DataEntryWidget

_DISTRIBUTOR_WIDGETS = {
    "Fuel Line":      FuelLineWidget,
    "Electrical Bus": ElectricalBusWidget,
    "Coolant Line":   CoolantLineWidget,
}

_TYPE_FROM_RCAIDE_CLASS = {
    "Fuel_Line":      "Fuel Line",
    "Electrical_Bus": "Electrical Bus",
    "Coolant_Line":   "Coolant Line",
}

# ----------------------------------------------------------------------------------------------------------------------
#  Distributor Frame
# ----------------------------------------------------------------------------------------------------------------------
from utilities import BTN_STYLE

class DistributorFrame(QWidget):
    """Frame that manages a list of distributor widgets (Fuel Line, Electrical Bus, Coolant Line).

    A type dropdown lets the user choose which distributor kind to add.
    ``load_data()`` detects the saved type from ``"distributor_type"`` (or,
    for legacy files, from ``"__type__"``) and instantiates the correct widget.
    ``refresh_connections()`` is called by ``PowertrainWidget`` whenever the
    propulsor or source lists change, forwarding the current names to each
    distributor's inline checkbox rows.
    """

    def __init__(self):
        super(DistributorFrame, self).__init__()

        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        self.distributor_sections_layout = QVBoxLayout()

        header_layout = QVBoxLayout()
        layout = self.create_scroll_layout()

        # ── Type dropdown + Add button ─────────────────────────────────────
        add_layout = QHBoxLayout()
        self.distributor_type_dropdown = QComboBox(self)
        self.distributor_type_dropdown.addItems(["Fuel Line", "Electrical Bus", "Coolant Line"])
        self.distributor_type_dropdown.setMinimumWidth(200)
        self.distributor_type_dropdown.currentTextChanged.connect(self._update_add_button_text)
        add_layout.addWidget(self.distributor_type_dropdown)

        self.add_distributor_button = QPushButton("Add Fuel Line", self)
        self.add_distributor_button.setStyleSheet(BTN_STYLE)
        self.add_distributor_button.setMinimumWidth(220)
        self.add_distributor_button.setMaximumWidth(280)
        self.add_distributor_button.clicked.connect(self.add_selected_distributor)
        add_layout.addWidget(self.add_distributor_button)
        add_layout.addStretch()
        header_layout.addLayout(add_layout)
        layout.addLayout(header_layout)

        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line_bar)

        layout.addLayout(self.distributor_sections_layout)
        layout.addLayout(QHBoxLayout())

        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    # ── Add / type dispatch ────────────────────────────────────────────────

    def _update_add_button_text(self, distributor_type):
        self.add_distributor_button.setText(f"Add {distributor_type}")

    def add_selected_distributor(self):
        dist_type = self.distributor_type_dropdown.currentText()
        self.distributor_sections_layout.addWidget(self._new_distributor_widget(dist_type))

    def _new_distributor_widget(self, dist_type, data_values=None):
        index = self.distributor_sections_layout.count()
        cls = _DISTRIBUTOR_WIDGETS.get(dist_type, FuelLineWidget)
        return cls(index, self.on_delete_button_pressed, data_values)

    def _distributor_type_from_data(self, data):
        explicit = data.get("distributor_type", "")
        if explicit in _DISTRIBUTOR_WIDGETS:
            return explicit
        type_str = data.get("__type__", "")
        class_name = type_str.rsplit(".", 1)[-1] if type_str else ""
        return _TYPE_FROM_RCAIDE_CLASS.get(class_name, "Fuel Line")

    # ── Data API ───────────────────────────────────────────────────────────

    def get_data_values(self):
        data = []
        distributors = []
        for index in range(self.distributor_sections_layout.count()):
            item = self.distributor_sections_layout.itemAt(index)
            if item is None:
                continue
            widget = item.widget()
            if not isinstance(widget, BaseDistributorWidget):
                continue
            distributor_data, distributor = widget.get_data_values()
            data.append(distributor_data)
            distributors.append(distributor)
        return data, distributors

    def load_data(self, data):
        while self.distributor_sections_layout.count():
            widget_item = self.distributor_sections_layout.itemAt(0)
            if widget_item is None:
                break
            widget = widget_item.widget()
            if widget is None:
                break
            self.distributor_sections_layout.removeWidget(widget)
            widget.deleteLater()

        for section_data in data:
            dist_type = self._distributor_type_from_data(section_data)
            self.distributor_sections_layout.addWidget(
                self._new_distributor_widget(dist_type, section_data)
            )

    def delete_data(self):
        pass

    def on_delete_button_pressed(self, index):
        item = self.distributor_sections_layout.itemAt(index)
        if item is None:
            return
        widget = item.widget()
        if widget is None:
            return
        widget.deleteLater()
        self.distributor_sections_layout.removeWidget(widget)
        self.distributor_sections_layout.update()

        for i in range(index, self.distributor_sections_layout.count()):
            item = self.distributor_sections_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, BaseDistributorWidget):
                widget.index = i

    def refresh_connections(self, propulsor_names: list[str], source_names: list[str]):
        """Push current propulsor and source names into each distributor's inline checkboxes."""
        for i in range(self.distributor_sections_layout.count()):
            item = self.distributor_sections_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, BaseDistributorWidget):
                widget.set_propulsors(propulsor_names)
                widget.set_sources(source_names)

    def set_save_function(self, function):
        self.save_function = function

    def create_scroll_layout(self):
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        self.setLayout(layout)
        return layout
