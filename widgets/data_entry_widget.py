from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QLineEdit, QLabel, QGridLayout, QWidget, QComboBox, QSizePolicy, QSpacerItem

from widgets.unit_picker_widget import UnitPickerWidget


class DataEntryWidget(QWidget):
    def __init__(self, data_units_labels):
        super(DataEntryWidget, self).__init__()
        self.data_units_labels = data_units_labels
        self.data_fields = {}

        self.init_ui()

    def init_ui(self):
        grid_layout = QGridLayout()
        for index, label in enumerate(self.data_units_labels):
            row, col = divmod(index, 2)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())
            # Set the width of the line edit
            # line_edit.setFixedWidth(150)  # Adjust the width as needed

            unit_picker = UnitPickerWidget(label[1])
            unit_picker.setFixedWidth(80)

            unit_combobox = QComboBox()
            unit_combobox.addItems(["m", "cm", "mm", "in", "ft"])

            grid_layout.addWidget(QLabel(label[0] + ":"), row, col * 4)
            grid_layout.addWidget(line_edit, row, col * 4 + 1, 1, 2)
            # Add a spacer
            grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), row,
                                col * 4 + 2)
            grid_layout.addWidget(unit_picker, row, col * 4 + 3, alignment=Qt.AlignmentFlag.AlignLeft)

            # Store a reference to the QLineEdit in the dictionary
            self.data_fields[label[0]] = (line_edit, unit_picker)

        grid_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(grid_layout)

    def clear_values(self):
        for key in self.data_fields:
            self.data_fields[key][0].setText("")
            self.data_fields[key][1].set_index(0)

    def get_values(self):
        data = {}
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value = float(line_edit.text()) if line_edit.text() else 0.0
            data[label] = value, unit_picker.current_index

        return data

    def load_data(self, data):
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value, index = data[label]
            line_edit.setText(str(value))
            unit_picker.set_index(index)
