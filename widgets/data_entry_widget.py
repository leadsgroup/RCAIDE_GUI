from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QLineEdit, QLabel, QGridLayout, QWidget, QSizePolicy, QSpacerItem,
    QCheckBox, QHBoxLayout, QVBoxLayout, QGroupBox, QToolButton, QFrame
)

from utilities import Units
from widgets import UnitPickerWidget


class DataEntryWidget(QWidget):
    def __init__(self, data_units_labels, num_cols=2, collapsible=False):
        """
        Initializes the DataEntryWidget.

        :param data_units_labels: List of tuples containing label and unit information.
        :param num_cols: Number of columns in the grid layout.
        :param collapsible: Boolean flag to enable/disable collapsibility.
        """
        super(DataEntryWidget, self).__init__()
        self.data_units_labels = data_units_labels
        self.data_fields = {}
        self.collapsed = False
        self.collapsible = collapsible  # New flag

        self.init_ui(num_cols)

    def init_ui(self, num_cols):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove outer margins for compactness

        if self.collapsible:
            # Create a horizontal layout for the collapse button and title (if any)
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            header_layout.setSpacing(5)  # Reduce spacing between elements

            self.collapse_button = QToolButton(self)
            self.collapse_button.setText('▼')
            self.collapse_button.setFixedSize(16, 16)  # Smaller button size
            self.collapse_button.setStyleSheet("QToolButton { padding: 0px; }")  # Remove padding
            self.collapse_button.clicked.connect(self.toggle_visibility)

            header_layout.addWidget(self.collapse_button, alignment=Qt.AlignmentFlag.AlignLeft)
            # Optionally, add a title or label next to the button
            # header_layout.addWidget(QLabel("Data Entry"), alignment=Qt.AlignmentFlag.AlignLeft)

            main_layout.addLayout(header_layout)

        self.content_group = QGroupBox(self)
        self.content_group.setStyleSheet("QGroupBox { margin-top: 0px; }")  # Reduce top margin

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(5, 5, 5, 5)  # Adjust margins as needed
        grid_layout.setSpacing(5)  # Reduce spacing between widgets

        self.content_group.setLayout(grid_layout)
        main_layout.addWidget(self.content_group)

        row, col = 0, 0
        for label in self.data_units_labels:
            grid_layout.setColumnStretch(col * 4 + 1, 1)

            if label[1] != Units.Heading:
                grid_layout.addWidget(QLabel(label[0] + ":"), row, col * 4)
            if label[1] == Units.Boolean:
                check_box = QCheckBox(self)
                check_box.setChecked(False)
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
                unit_picker.setFixedWidth(80)

                layout = QHBoxLayout()
                layout.setSpacing(2)  # Reduce spacing
                layout.addWidget(x_line_edit)
                layout.addWidget(y_line_edit)
                layout.addWidget(z_line_edit)

                x_line_edit.setMinimumSize(50, 0)
                y_line_edit.setMinimumSize(50, 0)
                z_line_edit.setMinimumSize(50, 0)

                grid_layout.addLayout(layout, row, col * 4 + 1, 1, 2)
                grid_layout.addWidget(
                    unit_picker, row, col * 4 + 3, alignment=Qt.AlignmentFlag.AlignLeft)

                self.data_fields[label[0]] = (
                    x_line_edit, y_line_edit, z_line_edit, unit_picker)
            elif label[1] == Units.Heading:
                row += 1 if col != 0 else 0
                layout = QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
                heading_layout = QVBoxLayout()
                heading_layout.setContentsMargins(0, 0, 0, 0)
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
                # Set the width of the line edit
                # line_edit.setFixedWidth(150)

                unit_picker = UnitPickerWidget(label[1])
                unit_picker.setFixedWidth(80)

                grid_layout.addWidget(line_edit, row, col * 4 + 1, 1, 2)
                # Add a spacer
                grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), row,
                                    col * 4 + 2)
                grid_layout.addWidget(
                    unit_picker, row, col * 4 + 3, alignment=Qt.AlignmentFlag.AlignLeft)

                # Store a reference to the QLineEdit in the dictionary
                self.data_fields[label[0]] = (line_edit, unit_picker)

            col = col + 1 if col < num_cols - 1 else 0
            if col == 0:
                row += 1
                grid_layout.setRowStretch(row, 1)

        # If not collapsible, ensure content is always visible
        if not self.collapsible:
            self.content_group.show()
        else:
            self.content_group.show()  # Initially expanded

    def toggle_visibility(self):
        """Toggle the visibility of the content_group when the button is clicked."""
        if self.collapsed:
            self.collapse_button.setText('▼')
            self.content_group.show()  # Expand
        else:
            self.collapse_button.setText('►')
            self.content_group.hide()  # Collapse
        self.collapsed = not self.collapsed

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

                x_value = float(x_line_edit.text()) if x_line_edit.text() else 0.0
                y_value = float(y_line_edit.text()) if y_line_edit.text() else 0.0
                z_value = float(z_line_edit.text()) if z_line_edit.text() else 0.0

                data[label] = [[x_value, y_value, z_value]], unit_picker.current_index
            elif self.data_units_labels[i][1] == Units.Heading:
                continue
            elif self.data_units_labels[i][1] == Units.Count:
                data_field = self.data_fields[label]
                line_edit, unit_picker = data_field
                value = int(line_edit.text()) if line_edit.text() else 0
                data[label] = value, unit_picker.current_index
            else:
                data_field = self.data_fields[label]
                line_edit, unit_picker = data_field
                value = float(line_edit.text()) if line_edit.text() else 0.0
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

                x_value = float(x_line_edit.text()) if x_line_edit.text() else 0.0
                y_value = float(y_line_edit.text()) if y_line_edit.text() else 0.0
                z_value = float(z_line_edit.text()) if z_line_edit.text() else 0.0

                x_value = unit_picker.apply_unit(x_value)
                y_value = unit_picker.apply_unit(y_value)
                z_value = unit_picker.apply_unit(z_value)

                data[label] = [[x_value, y_value, z_value]], unit_picker.current_index
            elif self.data_units_labels[i][1] == Units.Heading:
                continue
            elif self.data_units_labels[i][1] == Units.Count:
                data_field = self.data_fields[label]
                line_edit, unit_picker = data_field
                value = int(line_edit.text()) if line_edit.text() else 0
                data[label] = value, unit_picker.current_index
            else:
                data_field = self.data_fields[label]
                line_edit, unit_picker = data_field
                value = float(line_edit.text()) if line_edit.text() else 0.0
                data[label] = unit_picker.apply_unit(value), unit_picker.current_index
        return data

    def load_data(self, data):
        for i, label in enumerate(self.data_fields.keys()):
            if self.data_units_labels[i][1] == Units.Boolean:
                self.data_fields[label].setChecked(data[label][0])
            elif self.data_units_labels[i][1] == Units.Position:
                x_line_edit, y_line_edit, z_line_edit, unit_picker = self.data_fields[label]
                value, index = data[label]
                value = value[0]
                x_line_edit.setText(str(value[0]))
                y_line_edit.setText(str(value[1]))
                z_line_edit.setText(str(value[2]))
                unit_picker.set_index(index)
            elif self.data_units_labels[i][1] == Units.Heading:
                pass
            else:
                line_edit, unit_picker = self.data_fields[label]
                value, index = data[label]
                line_edit.setText(str(value))
                unit_picker.set_index(index)

    # TODO implement mark_save and changed_since_save
    def mark_save(self):
        pass

    def changed_since_save(self):
        pass