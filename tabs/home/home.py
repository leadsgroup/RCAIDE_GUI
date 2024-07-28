from os import link
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QPushButton, QSizePolicy, QSpacerItem, QWidget, QHBoxLayout, QVBoxLayout, QLabel

from utilities import create_line_bar
from widgets import Color
from tabs import TabWidget
from widgets.image_widget import ImageWidget


class HomeWidget(TabWidget):
    def __init__(self):
        super(HomeWidget, self).__init__()

        base_layout = QVBoxLayout()
        main_layout = QGridLayout()
        

        main_layout.addWidget(QPushButton("Website"), 0, 0)
        main_layout.addWidget(QPushButton("GitHub"), 0, 1)
        main_layout.addWidget(QPushButton("Documentation"), 0, 2)
        main_layout.addWidget(QPushButton("Contribute"), 0, 3)
        main_layout.addWidget(QPushButton("Contact"), 0, 4)
        
        main_layout.addWidget(ImageWidget("app_data/images/home_logo.png", w=1280, h=381), 1, 0, 1, 5, Qt.AlignmentFlag.AlignHCenter)
        # main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        base_layout.addLayout(main_layout)
        base_layout.addWidget(create_line_bar())
        
        start_layout = QVBoxLayout()
        flowchart_layout = QHBoxLayout()
        
        options = ["Boeing 737-800 mission", "Airbus A321neo mission", "ATR-72 mission", "Dash-8 Q400 mission"]
        aircraft_selector = QComboBox()
        aircraft_selector.addItems(options)
        
        quickstart_frame = QFrame()
        quickstart_layout = QVBoxLayout(quickstart_frame)
        quickstart_layout.addWidget(QLabel("Quickstart"))
        quickstart_layout.addWidget(aircraft_selector)
        quickstart_layout.addWidget(QPushButton("Load Aircraft"))
        quickstart_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        quickstart_frame.setFrameStyle(QFrame.Shape.Panel)
        start_layout.addWidget(quickstart_frame, 1)
        
        scratch_frame = QFrame()
        scratch_layout = QVBoxLayout(scratch_frame)
        scratch_layout.addWidget(QPushButton("Start from Scratch"))
        scratch_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        scratch_frame.setFrameStyle(QFrame.Shape.Panel)
        start_layout.addWidget(scratch_frame, 1)
        
        flowchart_layout.addLayout(start_layout)
        flowchart_layout.addWidget(ImageWidget("app_data/images/flowchart.png", w=800, h=1000))
        
        base_layout.addLayout(flowchart_layout)
        base_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.setLayout(base_layout)


def get_widget() -> QWidget:
    return HomeWidget()
