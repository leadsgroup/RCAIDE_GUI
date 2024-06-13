from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

from utilities import create_line_bar


# TODO: Add atmospheric analysis

class NoiseWidget(QWidget):
    def __init__(self):
        super(NoiseWidget, self).__init__()
        self.data_values = {}
        self.data_entry_layout = QVBoxLayout()

        self.create_scroll_area()

        self.main_layout.addWidget(QLabel("<b>Noise</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addLayout(self.data_entry_layout)
        self.main_layout.addWidget(create_line_bar())

        button_layout = QHBoxLayout()

        self.main_layout.addLayout(button_layout)

        # Adds scroll function
        self.main_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def create_scroll_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        self.main_layout = QVBoxLayout(scroll_content)
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout_scroll)
