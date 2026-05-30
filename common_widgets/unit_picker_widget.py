from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox

class UnitPickerWidget(QWidget):
    def __init__(self, unit_class):
        super(UnitPickerWidget, self).__init__()

        self.unit_class = unit_class()
        self.unit_list = self.unit_class.unit_list
        self.current_index = 0
        self.on_change_callback = None
        self._suppress_callback = False

        self.unit_picker = QComboBox()

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        unit_name_list = [unit[0] for unit in self.unit_list]
        self.unit_picker.addItems(unit_name_list)
        self.unit_picker.setCurrentIndex(self.current_index)
        self.unit_picker.currentIndexChanged.connect(self.on_unit_change)

        main_layout.addWidget(self.unit_picker)
        main_layout.setContentsMargins(0, 0, 0, 0)

    def on_unit_change(self, index):
        previous_index = self.current_index
        # Programmatic loads set the combo box without rewriting field values;
        # user-initiated changes ask the owning widget to convert the display.
        if (
            not self._suppress_callback
            and self.on_change_callback is not None
            and previous_index != index
        ):
            self.on_change_callback(previous_index, index)
        self.current_index = index

    def apply_unit(self, value):
        return self.unit_list[self.current_index][1](value)

    def set_index(self, index):
        self.current_index = index
        self._suppress_callback = True
        self.unit_picker.setCurrentIndex(index)
        self._suppress_callback = False
