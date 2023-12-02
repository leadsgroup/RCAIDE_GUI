from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from color import Color

class LandingGearFrame(QWidget):
    def __init__(self):
        super(LandingGearFrame, self).__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Landing Gear Frame"))
        layout.addWidget(Color("lightblue"))
        self.setLayout(layout)
