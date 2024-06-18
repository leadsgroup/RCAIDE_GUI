from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

from utilities import create_line_bar


# TODO: Add cost analysis

class CostsWidget(QWidget):
    def __init__(self):
        super(CostsWidget, self).__init__()
        self.data_values = {}
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Costs</b>"))
        self.main_layout.addWidget(create_line_bar())
        self.main_layout.addWidget(QLabel("Computes industrial and operating costs"))
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

