from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QLineEdit, QPushButton
from widgets.color import Color

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Create layouts
        base_layout = QVBoxLayout()

        # Create the horizontal layout for the title, input box, and "Add Dropdown" button
        horizontal_layout_title = QHBoxLayout()

        # Add a QLabel with the title "Energy Network Frame" to the left side of the horizontal layout
        title_label = QLabel("Mission Name:")
        horizontal_layout_title.addWidget(title_label)

        # Add a QLineEdit (input box) to the right side of the horizontal layout
        mission_name_input = QLineEdit(self)
        horizontal_layout_title.addWidget(mission_name_input)

        # Add both horizontal layouts to the main vertical layout
        base_layout.addLayout(horizontal_layout_title)

        # Create another horizontal layout for the "Select Mission Segment" label and the "Add Dropdown" button
        horizontal_layout_controls = QHBoxLayout()

        # Add a QLabel with the title to the left side of the horizontal layout
        segment_label = QLabel("Select Mission Segment")
        horizontal_layout_controls.addWidget(segment_label)

        # Add a QPushButton to add a new drop-down menu to the right side of the horizontal layout
        add_dropdown_button = QPushButton("Add Dropdown", self)
        add_dropdown_button.clicked.connect(self.add_dropdown)
        horizontal_layout_controls.addWidget(add_dropdown_button)

        # Add the horizontal layout with label and button to the main vertical layout
        base_layout.addLayout(horizontal_layout_controls)

        # Create color frames
        main_frame = Color("blue")
        main_extra_frame = Color("blue")

        # Add color frames to the main layout
        base_layout.addWidget(main_frame, 1)
        base_layout.addWidget(main_extra_frame, 3)

        # Initialize the list to store dynamically added QComboBoxes
        self.dynamic_comboboxes = []

        # Set spacings
        base_layout.setSpacing(3)

        # Set up the base widget
        base_widget = QWidget()
        base_widget.setLayout(base_layout)

        self.setLayout(base_layout)

    def add_dropdown(self):
        # Create a new QComboBox
        new_combobox = QComboBox(self)
        options = ["", "New Option 1", "New Option 2", "New Option 3"]
        new_combobox.addItems(options)

        # Add the new QComboBox to the layout
        self.layout().itemAt(1).layout().addWidget(new_combobox)  # Index 1 corresponds to the second layout

        # Store the reference to the dynamically added QComboBox
        self.dynamic_comboboxes.append(new_combobox)

def get_widget() -> QWidget:
    return MyWidget()
