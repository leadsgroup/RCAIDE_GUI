# RCAIDE_GUI/tabs/geometry/frames/powertrain/sources/energy_source_frame.py
#
# Created:  Dec 2025, M. Clarke

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
                              QSpacerItem, QSizePolicy, QFrame, QComboBox)

from tabs.geometry.widgets.powertrain.sources.fuel_tank_widget       import FuelTankWidget
from tabs.geometry.widgets.powertrain.sources.battery_module_widget  import BatteryModuleWidget
from common_widgets import DataEntryWidget

_SOURCE_WIDGETS = {
    "Fuel Tank":      FuelTankWidget,
    "Battery Module": BatteryModuleWidget,
}

_TYPE_FROM_RCAIDE_CLASS = {
    "Fuel_Tank":             "Fuel Tank",
    "Generic_Battery_Module":"Battery Module",
    "Lithium_Ion_NMC":       "Battery Module",
    "Lithium_Ion_LFP":       "Battery Module",
    "Lithium_Sulfur":        "Battery Module",
    "Aluminum_Air":          "Battery Module",
    "Lithium_Air":           "Battery Module",
}

# ----------------------------------------------------------------------------------------------------------------------
#  Energy Source Frame
# ----------------------------------------------------------------------------------------------------------------------
from utilities import BTN_STYLE

class EnergySourceFrame(QWidget):
    """Frame that manages a list of energy-source widgets (Fuel Tank, Battery Module).

    A type dropdown lets the user choose which source kind to add.
    ``load_data()`` detects the saved type from ``"source_type"`` (or, for
    files loaded from RCAIDE JSON, from ``"__type__"``) and instantiates the
    correct widget.  Both widget types expose ``"Source Name"`` so that
    ``PowertrainWidget._refresh_connections()`` can treat them uniformly when
    populating distributor checkboxes.
    """

    def __init__(self):
        super(EnergySourceFrame, self).__init__()

        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        self.source_sections_layout = QVBoxLayout()

        header_layout = QVBoxLayout()
        layout = self.create_scroll_layout()

        # ── Type dropdown + Add button ─────────────────────────────────────
        add_layout = QHBoxLayout()
        self.source_type_dropdown = QComboBox(self)
        self.source_type_dropdown.addItems(["Fuel Tank", "Battery Module"])
        self.source_type_dropdown.setMinimumWidth(200)
        self.source_type_dropdown.currentTextChanged.connect(self._update_add_button_text)
        add_layout.addWidget(self.source_type_dropdown)

        self.add_source_button = QPushButton("Add Fuel Tank", self)
        self.add_source_button.setStyleSheet(BTN_STYLE)
        self.add_source_button.setMinimumWidth(220)
        self.add_source_button.setMaximumWidth(280)
        self.add_source_button.clicked.connect(self.add_selected_source)
        add_layout.addWidget(self.add_source_button)
        add_layout.addStretch()
        header_layout.addLayout(add_layout)
        layout.addLayout(header_layout)

        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line_bar)

        layout.addLayout(self.source_sections_layout)
        layout.addLayout(QHBoxLayout())

        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    # ── Add / type dispatch ────────────────────────────────────────────────

    def _update_add_button_text(self, source_type):
        self.add_source_button.setText(f"Add {source_type}")

    def add_selected_source(self):
        src_type = self.source_type_dropdown.currentText()
        self.source_sections_layout.addWidget(self._new_source_widget(src_type))

    def _new_source_widget(self, src_type, data_values=None):
        index = self.source_sections_layout.count()
        cls = _SOURCE_WIDGETS.get(src_type, FuelTankWidget)
        return cls(index, self.on_delete_button_pressed, data_values)

    def _source_type_from_data(self, data):
        explicit = data.get("source_type", "")
        if explicit in _SOURCE_WIDGETS:
            return explicit
        type_str = data.get("__type__", "")
        class_name = type_str.rsplit(".", 1)[-1] if type_str else ""
        return _TYPE_FROM_RCAIDE_CLASS.get(class_name, "Fuel Tank")

    # ── Data API ───────────────────────────────────────────────────────────

    def get_data_values(self):
        data = []
        sources = []
        for index in range(self.source_sections_layout.count()):
            item = self.source_sections_layout.itemAt(index)
            if item is None:
                continue
            widget = item.widget()
            if not isinstance(widget, (FuelTankWidget, BatteryModuleWidget)):
                continue
            source_data, source = widget.get_data_values()
            data.append(source_data)
            sources.append(source)
        return data, sources

    def load_data(self, data):
        while self.source_sections_layout.count():
            widget_item = self.source_sections_layout.itemAt(0)
            if widget_item is None:
                break
            widget = widget_item.widget()
            if widget is None:
                break
            self.source_sections_layout.removeWidget(widget)
            widget.deleteLater()

        for section_data in data:
            src_type = self._source_type_from_data(section_data)
            self.source_sections_layout.addWidget(
                self._new_source_widget(src_type, section_data)
            )

    def delete_data(self):
        pass

    def on_delete_button_pressed(self, index):
        item = self.source_sections_layout.itemAt(index)
        if item is None:
            return
        widget = item.widget()
        if widget is None:
            return
        widget.deleteLater()
        self.source_sections_layout.removeWidget(widget)
        self.source_sections_layout.update()

        for i in range(index, self.source_sections_layout.count()):
            item = self.source_sections_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, (FuelTankWidget, BatteryModuleWidget)):
                widget.index = i

    def set_save_function(self, function):
        self.save_function = function

    def create_scroll_layout(self):
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        self.setLayout(layout)
        return layout
