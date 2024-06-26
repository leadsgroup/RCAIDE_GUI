from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class DefaultWidget(QWidget):
    def __init__(self):
        super(DefaultWidget, self).__init__()

        # Set the background color of the DefaultFrame
        # self.setAutoFillBackground(True)
        # palette = self.palette()
        # palette.setColor(QPalette.ColorRole.Window,
        #                  QColor(0, 0, 128))  # RGB Value For Navy. You can change it to any other color using RGB
        # self.setPalette(palette)

        # Create a QVBoxLayout for the DefaultFrame
        layout = QVBoxLayout(self)

        # Add a QLabel with the text to the layout
        label = QLabel("Please use the Dropdown Menu")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
