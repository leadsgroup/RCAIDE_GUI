from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from color import Color

class DefaultFrame(QWidget):
    def __init__(self):
        super(DefaultFrame, self).__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Please use the Dropdown Menu"))
        layout.addWidget(Color("lightblue"))
        self.setLayout(layout)
