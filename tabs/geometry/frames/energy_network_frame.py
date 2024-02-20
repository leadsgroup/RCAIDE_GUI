from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from tabs.geometry.frames.geometry_frame import GeometryFrame
from widgets.color import Color


class EnergyNetworkFrame(QWidget, GeometryFrame):
    def __init__(self):
        super(EnergyNetworkFrame, self).__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Energy Network Frame"))
        layout.addWidget(Color("lightblue"))
        self.setLayout(layout)
