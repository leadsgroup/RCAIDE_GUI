from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

# TODO: Add noise analysis

class NoiseFrame(QWidget):
    def __init__(self):
        super(NoiseFrame, self).__init__()
        self.data_values = {}
        self.data_entry_layout = QVBoxLayout()

        # Create a scroll area
        scroll_area = QScrollArea()
        # Allow the widget inside to resize with the scroll area
        scroll_area.setWidgetResizable(True)

        # Create a widget to contain the layout
        scroll_content = QWidget()
        # Set the main layout inside the scroll content
        layout = QVBoxLayout(scroll_content)

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Noise</b>"))

        layout.addLayout(header_layout)
        # layout.addWidget(Color("lightblue"))

        # Create a grid layout with 3 columns

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        layout.addLayout(self.data_entry_layout)

        # Add the layout for additional fuselage sections to the main layout

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Append All Fuselage Section Data Button
        # save_all_data_button = QPushButton("Save All Aerodynamics Data", self)
        # save_all_data_button.clicked.connect(self.append_all_data)
        # button_layout.addWidget(save_all_data_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)
