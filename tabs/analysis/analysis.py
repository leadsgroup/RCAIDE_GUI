from typing import cast

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QStackedLayout

from tabs.analysis.frames.aerodynamics_frame import AerodynamicsFrame
from tabs.analysis.frames.atmosphere_frame import AtmosphereFrame
from tabs.analysis.frames.costs_frame import CostsFrame
from tabs.analysis.frames.default_frame import DefaultFrame
from tabs.analysis.frames.energy_frame import EnergyFrame
from tabs.analysis.frames.noise_frame import NoiseFrame
from tabs.analysis.frames.planets_frame import PlanetsFrame
from tabs.analysis.frames.propulsion_frame import PropulsionFrame
from tabs.analysis.frames.stability_frame import StabilityFrame
from tabs.analysis.frames.weights_frame import WeightsFrame


class AnalysisWidget(QWidget):

    def __init__(self):
        super(AnalysisWidget, self).__init__()

        base_layout = QHBoxLayout()
        main_layout = QStackedLayout()
        # Define actions based on the selected index
        self.frames = [DefaultFrame, AerodynamicsFrame, AtmosphereFrame, CostsFrame, EnergyFrame, NoiseFrame,
                       PlanetsFrame, PropulsionFrame, StabilityFrame, WeightsFrame]

        for frame in self.frames:
            main_layout.addWidget(frame())

        self.tree_frame = QWidget()
        # self.main_extra_frame = None  # Initialize as None

        self.tree_frame_layout = QVBoxLayout(self.tree_frame)

        # Set a background color for tree_frame
        # tree_frame_style = """
        #     background-color: navy
        # """
        # self.tree_frame.setStyleSheet(tree_frame_style)

        # Create a QComboBox and add options
        self.dropdown = QComboBox()
        options = ["Select an option", "Aerodynamics", "Atmospheric", "Costs", "Energy", "Noise",
                   "Planets", "Propulsion", "Stability", "Weights"]
        self.dropdown.addItems(options)

        self.tree_frame_layout.addWidget(self.dropdown, alignment=Qt.AlignmentFlag.AlignTop)

        # main_layout.addWidget(Color("navy"), 7)
        base_layout.addWidget(self.tree_frame, 1)
        base_layout.addLayout(main_layout, 4)

        main_layout.setSpacing(3)
        base_layout.setSpacing(3)

        main_layout.setCurrentIndex(0)

        self.setLayout(base_layout)

        # Connect the dropdown's currentIndexChanged signal to a slot
        self.dropdown.currentIndexChanged.connect(self.on_dropdown_change)

        # Initially display the DefaultFrame

    def on_dropdown_change(self, index):
        layout = self.layout()
        if layout is not None:
            main_layout: QStackedLayout = cast(QStackedLayout, layout.itemAt(1))
            main_layout.setCurrentIndex(index)


def get_widget() -> QWidget:
    return AnalysisWidget()
