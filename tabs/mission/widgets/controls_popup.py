from PyQt6.QtWidgets import QVBoxLayout, QDialog, QComboBox, QHBoxLayout

class ControlsPopup(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Control Systems')
        # Set the size of the popup window

        self.setFixedSize(800, 600)  # Set a fixed size
        main_layout = QVBoxLayout()
        Hlayout = QHBoxLayout()

        # Create the dropdown
        dropdown = QComboBox()
        dropdown.addItem("Option 1")
        dropdown.addItem("Option 2")
        dropdown.addItem("Option 3")

        

        Hlayout.addWidget(dropdown)
        main_layout.addLayout(Hlayout)
        self.setLayout(main_layout)
