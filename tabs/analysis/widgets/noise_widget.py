from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox

from utilities import create_line_bar, Units
from widgets import DataEntryWidget


# TODO: Add noise analysis

class NoiseWidget(QWidget):
    data_units_labels = [
        [
            ("Flyover", Units.Boolean),
            ("Approach", Units.Boolean),
            ("Sideline", Units.Boolean),
            ("Sideline X Position", Units.Length),
            ("Print Noise Output", Units.Boolean),
            ("Mean Sea Level Altitude", Units.Boolean),
            ("Aircraft Departure Location", Units.Position),
            ("Aircraft Destination Location", Units.Position),
            ("Microphone X Resolution", Units.Count),
            ("Microphone Y Resolution", Units.Count),
            # TODO ("Microphone X Stencil", Units.Length),
            # TODO ("Microphone Y Stencil", Units.Length),
            ("Microphone Min X", Units.Length),
            ("Microphone Max X", Units.Length),
            ("Microphone Min Y", Units.Length),
            ("Microphone Max Y", Units.Length),
            ("Noise Hemisphere", Units.Boolean),
            ("Noise Hemisphere Radius", Units.Length),
            ("Noise Hemisphere Microphone Resolution", Units.Count),
            ("Noise Hemisphere Phi Upper Bound", Units.Angle),
            ("Noise Hemisphere Phi Lower Bound", Units.Angle),
            ("Noise Hemisphere Theta Upper Bound", Units.Angle),
            ("Noise Hemisphere Theta Lower Bound", Units.Angle),
        ],
        [
            ("Sideline X Position", Units.Length),
            ("Print Noise Output", Units.Boolean),
            ("Mean Sea Level Altitude", Units.Boolean),
            ("Aircraft Departure Location", Units.Position),
            ("Aircraft Destination Location", Units.Position),
            ("Microphone X Resolution", Units.Count),
            ("Microphone Y Resolution", Units.Count),
            # TODO ("Microphone X Stencil", Units.Length),
            # TODO ("Microphone Y Stencil", Units.Length),
            ("Microphone Min X", Units.Length),
            ("Microphone Max X", Units.Length),
            ("Microphone Min Y", Units.Length),
            ("Microphone Max Y", Units.Length),
            ("Noise Hemisphere", Units.Boolean),
            ("Noise Hemisphere Radius", Units.Length),
            ("Noise Hemisphere Microphone Resolution", Units.Count),
            ("Noise Hemisphere Phi Upper Bound", Units.Angle),
            ("Noise Hemisphere Phi Lower Bound", Units.Angle),
            ("Noise Hemisphere Theta Upper Bound", Units.Angle),
            ("Noise Hemisphere Theta Lower Bound", Units.Angle),]
    ]
    analyses = ["Correlation Buildup", "Frequency Domain Buildup"]

    def __init__(self):
        super(NoiseWidget, self).__init__()
        self.data_values = {}
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Noise</b>"))
        self.main_layout.addWidget(create_line_bar())

        analysis_selector = QComboBox()
        analysis_selector.addItems(self.analyses)
        analysis_selector.currentIndexChanged.connect(self.on_analysis_change)
        self.main_layout.addWidget(analysis_selector)
        
        self.data_entry_widget = DataEntryWidget(self.data_units_labels[0])
        self.main_layout.addWidget(self.data_entry_widget)

        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def on_analysis_change(self, index):
        print("Index changed to", index)

        assert self.main_layout is not None

        self.main_layout.removeWidget(self.data_entry_widget)
        self.data_entry_widget = DataEntryWidget(self.data_units_labels[index])
        # self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.insertWidget(
            self.main_layout.count() - 1, self.data_entry_widget)
