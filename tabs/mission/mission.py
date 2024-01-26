from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLineEdit

from widgets.color import Color


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Create layouts
        base_layout = QHBoxLayout()
        main_layout = QVBoxLayout()

        # Create color frames
        tree_frame = Color("blue")
        main_frame = Color("blue")
        main_extra_frame = Color("blue")

        # Add color frames to main layout
        main_layout.addWidget(main_frame, 7)
        main_layout.addWidget(main_extra_frame, 3)

        # Create a QLineEdit for the label
        self.label_input = QLineEdit(self)

        # Create a combo box
        self.comboBox = QComboBox(self)

        # Add items to the combo box
        options = ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5", "Option 6"]
        self.comboBox.addItems(options)

        # Connect the combo box's currentIndexChanged signal to a custom function
        self.comboBox.currentIndexChanged.connect(self.on_option_selected)

        # Add the label input and combo box to the main layout
        main_layout.addWidget(self.label_input)
        main_layout.addWidget(self.comboBox)

        # Add tree frame and main layout to base layout
        base_layout.addWidget(tree_frame, 1)
        base_layout.addLayout(main_layout, 4)

        # Set spacings
        main_layout.setSpacing(3)
        base_layout.setSpacing(3)

        # Set up the base widget
        base_widget = QWidget()
        base_widget.setLayout(base_layout)

        self.setLayout(base_layout)

    def on_option_selected(self, index):
        selected_option = self.comboBox.itemText(index)
        print(f"Option selected: {selected_option}")


def get_widget() -> QWidget:
    return MyWidget()