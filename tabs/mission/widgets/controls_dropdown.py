import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QDialog, QComboBox, QHBoxLayout

class ControlsDropdown(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Control Systems')
        self.setFixedSize(800, 600)  # Set a fixed size

        # Create the main layout
        main_layout = QVBoxLayout()

        # Create the dropdown
        dropdown = QComboBox()
        dropdown.addItem("Option 1")
        dropdown.addItem("Option 2")
        dropdown.addItem("Option 3")

        # Add the dropdown to the layout
        main_layout.addWidget(dropdown)

        # Create the button to toggle visibility
        self.toggle_button = QPushButton("Toggle Dropdown")
        self.toggle_button.clicked.connect(self.toggle_visibility)

        # Add the button to the layout
        main_layout.addWidget(self.toggle_button)

        # Set the main layout for the dialog
        self.setLayout(main_layout)

    def toggle_visibility(self):
        # Toggle the visibility of the dialog
        if self.isVisible():
            self.hide()
        else:
            self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlsDropdown()
    window.show()
    sys.exit(app.exec())

        