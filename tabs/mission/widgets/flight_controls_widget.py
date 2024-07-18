from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget, QCheckBox, QSizePolicy

from utilities import Units, create_line_bar
from widgets import DataEntryWidget


class FlightControlsWidget(QWidget):
    def __init__(self):
        super().__init__()
        base_layout = QVBoxLayout()

        toggles_layout = QHBoxLayout()
        for key, toggles in self.fields.items():
            sub_layout = QVBoxLayout()

            header = QLabel("<b>" + key + "</b>")
            header.setSizePolicy(QSizePolicy.Policy.Minimum,
                                 QSizePolicy.Policy.Minimum)
            sub_layout.addWidget(header)
            sub_layout.addWidget(create_line_bar())

            for toggle in toggles:
                check_box = QCheckBox(toggle)
                check_box.setSizePolicy(
                    QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding)
                sub_layout.addWidget(check_box)

            toggles_layout.addLayout(sub_layout, 1)

        base_layout.addLayout(toggles_layout)

        self.setLayout(base_layout)

    fields = {
        "Autopilot": [
            ("Body Angle"),
            ("Bank Angle"),
            ("Wind Angle"),
            ("Velocity"),
            ("Acceleration"),
            ("Altitude"),
        ],
        "Control Surfaces": [
            ("Elevator Deflection"),
            ("Rudder Deflection"),
            ("Flap Deflection"),
            ("Slat Deflection"),
            ("Aileron Deflection"),
        ],
        "Propulsion": [
            ("Throttle"),
            ("Thrust Vector Angle"),
            ("Blade Pitch Angle"),
        ]
    }
