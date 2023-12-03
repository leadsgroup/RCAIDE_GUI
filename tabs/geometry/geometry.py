from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox



from widgets.color import Color
from tabs.frames.default_frame import DefaultFrame
from tabs.frames.wings_frame import WingsFrame
from tabs.frames.fuselage_frame import FuselageFrame
from tabs.frames.nacelle_frame import NacellesFrame
from tabs.frames.landing_gear_frame import LandingGearFrame
from tabs.frames.energy_network_frame import EnergyNetworkFrame


class GeometryWidget(QWidget):
    def __init__(self):
        super(GeometryWidget, self).__init__()

        base_layout = QHBoxLayout()
        main_layout = QVBoxLayout()

        self.tree_frame = QWidget()
        self.main_extra_frame = None  # Initialize as None

        self.tree_frame_layout = QVBoxLayout(self.tree_frame)
        
        # Set a background color for tree_frame
        tree_frame_style = """
            background-color: navy
        """
        self.tree_frame.setStyleSheet(tree_frame_style)
        
        # Create a QComboBox and add options
        self.dropdown = QComboBox()
        options = ["Select an option", "Add Fuselage", "Add Wings", "Add Nacelles", "Add Landing Gear", "Add Energy Network"]
        self.dropdown.addItems(options)
        
        # Style the dropdown with a colored background
        dropdown_style = """
            QComboBox {
                background-color: coral;
                border: 1px solid #5A5A5A;
                padding: 2px;
            }

            QComboBox QAbstractItemView {
                background-color: goldenrod;  /* You can adjust the color here */
                border: 1px solid #5A5A5A;
            }
        """
        self.dropdown.setStyleSheet(dropdown_style)
        
        self.tree_frame_layout.addWidget(self.dropdown, alignment=Qt.AlignmentFlag.AlignTop)

        main_layout.addWidget(Color("navy"), 7)
        main_layout.addWidget(self.main_extra_frame, 3)
        base_layout.addWidget(self.tree_frame, 1)
        base_layout.addLayout(main_layout, 4)

        main_layout.setSpacing(3)
        base_layout.setSpacing(3)

        self.setLayout(base_layout)

        # Connect the dropdown's currentIndexChanged signal to a slot
        self.dropdown.currentIndexChanged.connect(self.on_dropdown_change)

    def on_dropdown_change(self, index):
        # Define actions based on the selected index
        frames = [DefaultFrame, FuselageFrame, WingsFrame, NacellesFrame, LandingGearFrame, EnergyNetworkFrame]

        if 0 <= index < len(frames):
            # Replace main_extra_frame with the selected frame
            new_frame = frames[index]()
            self.replace_main_extra_frame(new_frame)

    def replace_main_extra_frame(self, new_frame):
        old_frame = self.main_extra_frame
    
        if old_frame is not None:
            main_layout = self.layout().itemAt(1)  # Assuming main_extra_frame is at index 1
    
            if main_layout is not None:
                # Remove the old frame from the layout
                main_layout.removeWidget(old_frame)
                old_frame.setParent(None)
    
        # Add the new frame to the layout
        main_layout = self.layout().itemAt(1)  # Assuming main_extra_frame is at index 1
        main_layout.addWidget(new_frame, 3)
    
        # Update the reference to the current main_extra_frame
        self.main_extra_frame = new_frame








def get_widget() -> QWidget:
    return GeometryWidget()