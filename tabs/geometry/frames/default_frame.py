from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from tabs.geometry.frames import GeometryFrame


class DefaultFrame(GeometryFrame):
    def __init__(self):
        super(DefaultFrame, self).__init__()

        # Create a QVBoxLayout for the DefaultFrame
        layout = QVBoxLayout(self)

        # Add a QLabel with the text to the layout
        label = QLabel("Please select or create a configuration to begin!")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
