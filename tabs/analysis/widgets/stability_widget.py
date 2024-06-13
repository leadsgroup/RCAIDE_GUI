from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

from utilities import create_line_bar


class StabilityWidget(QWidget):
    def __init__(self):
        super(StabilityWidget, self).__init__()
        self.data_values = {}
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Stability</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(QLabel("VLM Perturbation Method"))
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)
