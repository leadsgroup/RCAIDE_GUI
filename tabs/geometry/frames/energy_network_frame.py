from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from widgets.color import Color


class EnergyNetworkFrame(QWidget):
    def __init__(self):
        super(EnergyNetworkFrame, self).__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Energy Network Frame"))
        layout.addWidget(Color("lightblue"))
        self.setLayout(layout)
