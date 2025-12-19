from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, \
    QSizePolicy, QSpacerItem

from tabs.geometry.widgets.powertrain.modulator import ModulatorWidget
from widgets import DataEntryWidget


class ModulatorFrame(QWidget):
    def __init__(self):
        super(ModulatorFrame, self).__init__()

        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        # List to store data values modulator_ sections
        self.modulator_sections_layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QVBoxLayout()
        # label = QLabel("<u><b>modulator Frame</b></u>")

        layout = self.create_scroll_layout()

        # header_layout.addWidget(label)

        # Add modulator_ Section Button
        #add_section_button = QPushButton("Add Modulator", self)
        #add_section_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        #add_section_button.setMaximumWidth(200)
        #add_section_button.clicked.connect(self.add_modulator_section)c
        #header_layout.addWidget(add_section_button)

        layout.addLayout(header_layout)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

     