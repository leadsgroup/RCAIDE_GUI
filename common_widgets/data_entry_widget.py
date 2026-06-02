# RCAIDE_GUI/tabs/visualize_geometry/features/axes_gizmo.py

# Created: M Clarke, LEADS, 2024
# Python imports
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QLineEdit, QLabel, QGridLayout, QWidget, QSizePolicy, QSpacerItem, QCheckBox, QHBoxLayout, \
    QVBoxLayout

from utilities import Units
from common_widgets import UnitPickerWidget

# ------------------------------------------------------------------------------
# Data Entry Widget
# ------------------------------------------------------------------------------
class DataEntryWidget(QWidget):
    # Emitted when the user finishes editing any field or changes a unit.
    # Safe to connect to save_data — does NOT fire during programmatic load_data calls.
    data_changed = pyqtSignal()

    def __init__(self, data_units_labels, num_cols=2):
        super(DataEntryWidget, self).__init__()
        self.data_units_labels = data_units_labels
        self.data_fields = {}

        self.init_ui(num_cols)

    def init_ui(self, num_cols):
        grid_layout = QGridLayout()
        row, col = 0, 0
        for label in self.data_units_labels:
            grid_layout.setColumnStretch(col * 4 + 1, 1)

            if label[1] != Units.Heading:
                grid_layout.addWidget(QLabel(label[0] + ":"), row, col * 4)
            if label[1] == Units.Boolean:
                check_box = QCheckBox(self)
                check_box.setChecked(False)
                check_box.stateChanged.connect(lambda _: self.data_changed.emit())
                grid_layout.addWidget(check_box, row, col * 4 + 1, 1, 2)
                self.data_fields[label[0]] = check_box
            elif label[1] == Units.Position:
                x_line_edit = QLineEdit(self)
                y_line_edit = QLineEdit(self)
                z_line_edit = QLineEdit(self)

                x_line_edit.setValidator(QDoubleValidator())
                y_line_edit.setValidator(QDoubleValidator())
                z_line_edit.setValidator(QDoubleValidator())

                unit_picker = UnitPickerWidget(Units.Length)
                unit_picker.on_change_callback = self._make_unit_change_handler(
                    unit_picker, x_line_edit, y_line_edit, z_line_edit
                )
                # Also emit data_changed when unit changes (fires only on user action,
                # not during load_data, because UnitPickerWidget._suppress_callback guards it).
                _conv_cb = unit_picker.on_change_callback
                unit_picker.on_change_callback = lambda p, n, _cb=_conv_cb: (_cb(p, n), self.data_changed.emit())
                unit_picker.setFixedWidth(80)

                layout = QHBoxLayout()
                layout.addWidget(x_line_edit)
                layout.addWidget(y_line_edit)
                layout.addWidget(z_line_edit)

                x_line_edit.setMinimumSize(50, 0)
                y_line_edit.setMinimumSize(50, 0)
                z_line_edit.setMinimumSize(50, 0)

                # editingFinished fires on Enter/Tab — not on programmatic setText.
                x_line_edit.editingFinished.connect(self.data_changed)
                y_line_edit.editingFinished.connect(self.data_changed)
                z_line_edit.editingFinished.connect(self.data_changed)

                grid_layout.addLayout(layout, row, col * 4 + 1, 1, 2)
                grid_layout.addWidget(
                    unit_picker, row, col * 4 + 3, alignment=Qt.AlignmentFlag.AlignLeft)

                self.data_fields[label[0]] = (
                    x_line_edit, y_line_edit, z_line_edit, unit_picker)
            elif label[1] == Units.Heading:
                row += 1 if col != 0 else 0
                layout = QHBoxLayout()
                heading_layout = QVBoxLayout()
                heading_label = QLabel(label[0])
                font = heading_label.font()
                font.setBold(True)
                font.setUnderline(True)
                heading_label.setFont(font)
                heading_layout.addWidget(heading_label)
                layout.addLayout(heading_layout)
                grid_layout.addLayout(layout, row, 0, 1, 4)
                col = num_cols - 1
                self.data_fields[label[0]] = ()
            else:
                line_edit = QLineEdit(self)
                line_edit.setValidator(QDoubleValidator())
                line_edit.setMinimumWidth(150)

                unit_picker = UnitPickerWidget(label[1])
                unit_picker.on_change_callback = self._make_unit_change_handler(
                    unit_picker, line_edit
                )
                _conv_cb = unit_picker.on_change_callback
                unit_picker.on_change_callback = lambda p, n, _cb=_conv_cb: (_cb(p, n), self.data_changed.emit())
                unit_picker.setFixedWidth(80)

                line_edit.editingFinished.connect(self.data_changed)

                grid_layout.addWidget(line_edit, row, col * 4 + 1, 1, 2)
                grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), row,
                                    col * 4 + 2)
                grid_layout.addWidget(
                    unit_picker, row, col * 4 + 3, alignment=Qt.AlignmentFlag.AlignLeft)

                self.data_fields[label[0]] = (line_edit, unit_picker)

            col = col + 1 if col < num_cols - 1 else 0
            if col == 0:
                row += 1
                grid_layout.setRowStretch(row, 1)

        grid_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(grid_layout)

    @staticmethod
    def _apply_unit_at(unit_picker, index, value):
        return unit_picker.unit_list[index][1](value)

    @staticmethod
    def _display_value_from_si(unit_picker, index, si_value):
        # Unit converters map display values into RCAIDE/base units; invert
        # that linear conversion to show the same value in the selected unit.
        converter = unit_picker.unit_list[index][1]
        zero = converter(0.0)
        one = converter(1.0)
        scale = one - zero
        if scale == 0:
            return si_value
        return (si_value - zero) / scale

    @staticmethod
    def _format_converted_value(value):
        return f"{value:.15g}"

    def _make_unit_change_handler(self, unit_picker, *line_edits):
        def convert_display_values(previous_index, new_index):
            for line_edit in line_edits:
                text = line_edit.text()
                if not text:
                    continue

                try:
                    old_display_value = float(text)
                except ValueError:
                    continue

                # Preserve the stored physical value while changing only how
                # the current text is displayed, e.g. radians <-> degrees.
                si_value = self._apply_unit_at(
                    unit_picker, previous_index, old_display_value
                )
                new_display_value = self._display_value_from_si(
                    unit_picker, new_index, si_value
                )
                line_edit.setText(self._format_converted_value(new_display_value))

        return convert_display_values

    def clear_values(self):
        for i, key in enumerate(self.data_fields.keys()):
            if self.data_units_labels[i][1] == Units.Boolean:
                self.data_fields[key].setChecked(False)
            elif self.data_units_labels[i][1] == Units.Position:
                self.data_fields[key][0].setText("")
                self.data_fields[key][1].setText("")
                self.data_fields[key][2].setText("")
                self.data_fields[key][3].set_index(0)
            elif self.data_units_labels[i][1] == Units.Heading:
                continue
            else:
                self.data_fields[key][0].setText("")
                self.data_fields[key][1].set_index(0)

    def get_values(self):
        data = {}
        for i, label in enumerate(self.data_fields.keys()):
            # Find corresponding unit
            if self.data_units_labels[i][1] == Units.Boolean:
                data_field = self.data_fields[label]
                data[label] = (data_field.isChecked(), 0)
            elif self.data_units_labels[i][1] == Units.Position:
                data_field = self.data_fields[label]
                x_line_edit, y_line_edit, z_line_edit, unit_picker = data_field

                x_value = float(x_line_edit.text()
                                ) if x_line_edit.text() else 0.0
                y_value = float(y_line_edit.text()
                                ) if y_line_edit.text() else 0.0
                z_value = float(z_line_edit.text()
                                ) if z_line_edit.text() else 0.0

                data[label] = [[x_value, y_value,
                               z_value]], unit_picker.current_index
            elif self.data_units_labels[i][1] == Units.Heading:
                continue
            elif self.data_units_labels[i][1] == Units.Count:
                data_field = self.data_fields[label]
                line_edit, unit_picker = data_field
                text = line_edit.text()
                value = int(text) if text else 0
                data[label] = value, unit_picker.current_index
            else:
                data_field = self.data_fields[label]
                line_edit, unit_picker = data_field
                text = line_edit.text()
                value = float(text) if text else None
                data[label] = value, unit_picker.current_index
        return data

    def get_values_si(self):
        data = {}
        for i, label in enumerate(self.data_fields.keys()):
            if self.data_units_labels[i][1] == Units.Boolean:
                data_field = self.data_fields[label]
                data[label] = (data_field.isChecked(), 0)
            elif self.data_units_labels[i][1] == Units.Position:
                data_field = self.data_fields[label]
                x_line_edit, y_line_edit, z_line_edit, unit_picker = data_field

                x_value = float(x_line_edit.text()
                                ) if x_line_edit.text() else 0.0
                y_value = float(y_line_edit.text()
                                ) if y_line_edit.text() else 0.0
                z_value = float(z_line_edit.text()
                                ) if z_line_edit.text() else 0.0

                x_value, y_value, z_value = unit_picker.apply_unit(
                    x_value), unit_picker.apply_unit(y_value), unit_picker.apply_unit(z_value)

                data[label] = [[x_value, y_value,
                               z_value]], unit_picker.current_index
            elif self.data_units_labels[i][1] == Units.Heading:
                continue
            elif self.data_units_labels[i][1] == Units.Count:
                data_field = self.data_fields[label]
                line_edit, unit_picker = data_field
                text = line_edit.text()
                value = int(text) if text else 0
                data[label] = value, unit_picker.current_index
            else:
                data_field = self.data_fields[label]
                line_edit, unit_picker = data_field
                text = line_edit.text()
                value = unit_picker.apply_unit(float(text)) if text else None
                data[label] = value, unit_picker.current_index
        return data

    def load_data(self, data):
        for i, label in enumerate(self.data_fields.keys()):
            if self.data_units_labels[i][1] == Units.Boolean:
                self.data_fields[label].setChecked(data[label][0])
            elif self.data_units_labels[i][1] == Units.Position:
                x_line_edit, y_line_edit, z_line_edit, unit_picker = self.data_fields[label]
                value, index = data[label]
                if isinstance(value, list) and value and isinstance(value[0], list):
                    value = value[0]
                elif not isinstance(value, list):
                    value = [0, 0, 0]
                x_line_edit.setText(str(value[0]))
                y_line_edit.setText(str(value[1]))
                z_line_edit.setText(str(value[2]))
                unit_picker.set_index(index)
            elif self.data_units_labels[i][1] == Units.Heading:
                pass
            else:
                line_edit, unit_picker = self.data_fields[label]
                value, index = data[label]
                line_edit.setText("" if value is None else str(value))
                unit_picker.set_index(index)
    
    # TODO implement mark_save and changed_since_save
    def mark_save(self):
        pass
    
    def changed_since_save(self):
        pass
