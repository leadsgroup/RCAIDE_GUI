from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox


class UnitPickerWidget(QWidget):
    def __init__(self, unit_class):
        super(UnitPickerWidget, self).__init__()

        self.unit_class = unit_class()
        self.unit_list = self.unit_class.unit_list
        self.current_index = 0

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
        self.current_index = index
        print(f"Unit changed to {self.unit_list[index][0]}")

    def apply_unit(self, value):
        return self.unit_list[self.current_index][1](value)

    def set_index(self, index):
        self.current_index = index
        self.unit_picker.setCurrentIndex(index)
        print(f"Unit changed to {self.unit_list[index][0]}")
