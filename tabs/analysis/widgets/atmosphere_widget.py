from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox

from utilities import create_line_bar


class AtmosphereWidget(QWidget):
    def __init__(self):
        super(AtmosphereWidget, self).__init__()
        self.data_values = {}
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Atmosphere</b>"))
        self.main_layout.addWidget(create_line_bar())

        options = ["1976 US Standard Atmosphere", "Constant Temperature"]
        atmosphere_selector = QComboBox()
        atmosphere_selector.addItems(options)
        
        self.main_layout.addWidget(atmosphere_selector)
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)
