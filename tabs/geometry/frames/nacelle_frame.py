from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from widgets.color import Color


class NacellesFrame(QWidget):
    def __init__(self):
        super(NacellesFrame, self).__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nacelles Frame"))
        layout.addWidget(Color("lightblue"))
        self.setLayout(layout)
