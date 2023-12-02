from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from color import Color

class WingsFrame(QWidget):
    def __init__(self):
        super(WingsFrame, self).__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Wings Frame"))
        layout.addWidget(Color("lightblue"))
        self.setLayout(layout)
