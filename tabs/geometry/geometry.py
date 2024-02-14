from typing import cast

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QStackedLayout, QTreeWidget, QTreeWidgetItem

from tabs.geometry.frames.default_frame import DefaultFrame
from tabs.geometry.frames.energy_network_frame import EnergyNetworkFrame
from tabs.geometry.frames.fuselage_frame import FuselageFrame
from tabs.geometry.frames.landing_gear_frame import LandingGearFrame
from tabs.geometry.frames.nacelle_frame import NacelleFrame
from tabs.geometry.frames.wings_frame import WingsFrame


class GeometryWidget(QWidget):
    def __init__(self):
        super(GeometryWidget, self).__init__()

        base_layout = QHBoxLayout()
        main_layout = QStackedLayout()
        self.tree_frame_layout = QVBoxLayout()

        # Define actions based on the selected index
        self.frames = [DefaultFrame, FuselageFrame, WingsFrame, NacelleFrame, LandingGearFrame, EnergyNetworkFrame]
        self.tabs = ["Fuselage", "Wings", "Nacelle", "Landing Gear", "Energy Network"]
        options = ["Select an option", "Add Fuselage", "Add Wings", "Add Nacelles", "Add Landing Gear",
                   "Add Energy Network"]

        for frame in self.frames:
            main_layout.addWidget(frame())

        # Create a QComboBox and add options
        self.dropdown = QComboBox()
        self.dropdown.addItems(options)
        self.dropdown.currentIndexChanged.connect(self.on_dropdown_change)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Vehicle Elements"])

        for tab in self.tabs:
            item = QTreeWidgetItem([f"{tab}"])
            self.tree.addTopLevelItem(item)

        self.tree_frame_layout.addWidget(self.dropdown)
        self.tree_frame_layout.addWidget(self.tree)

        # Make the dropdown take as little space as possible and make the tree frame take as much space as possible
        # self.dropdown.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum))
        # self.tree.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))

        # main_layout.addWidget(Color("navy"), 7)
        base_layout.addLayout(self.tree_frame_layout, 1)
        base_layout.addLayout(main_layout, 4)

        main_layout.setSpacing(3)
        base_layout.setSpacing(3)

        # Initially display the DefaultFrame
        main_layout.setCurrentIndex(0)

        self.setLayout(base_layout)

    def on_dropdown_change(self, index):
        layout = self.layout()
        if layout:
            main_layout: QStackedLayout = cast(QStackedLayout, layout.itemAt(1))
            main_layout.setCurrentIndex(index)


def get_widget() -> QWidget:
    return GeometryWidget()
