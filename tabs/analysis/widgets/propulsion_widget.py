from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox

from utilities import create_line_bar


class PropulsionWidget(QWidget):
    def __init__(self):
        super(PropulsionWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Propulsion</b>"))
        self.main_layout.addWidget(create_line_bar())

        options = ["Rotor Wake Fidelity 0",
                   "Rotor Wake Fidelity 1", "Rotor Wake Fidelity 2"]
        propulsion_selector = QComboBox()
        propulsion_selector.addItems(options)

        self.main_layout.addWidget(propulsion_selector)
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)
