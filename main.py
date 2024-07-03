import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from tabs import *
from tabs.aircraft_configs.aircraft_configs import AircraftConfigsWidget


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RCAIDE")

        menubar = self.menuBar()
        if menubar is None:
            return

        # File menu
        file_menu = menubar.addMenu("File")
        if file_menu is None:
            return

        file_menu.addAction("New")
        file_menu.addAction("Open")
        file_menu.addAction("Save")
        file_menu.addSeparator()

        file_menu.addSeparator()
        file_menu.addAction("Quit")

        # Other menus
        menubar.addMenu("Edit")
        menubar.addMenu("View")
        menubar.addMenu("Help")

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        # tabs.setMovable(True)

        self.tabs.currentChanged.connect(self.on_tab_change)

        self.tabs.addTab(home.get_widget(), "Home")
        geometry_widget = geometry.get_widget()
        self.tabs.addTab(geometry_widget, "Geometry")
        self.tabs.addTab(aircraft_configs.get_widget(
            geometry_widget), "Aircraft Configurations")
        self.tabs.addTab(analysis.get_widget(), "Analysis")
        self.tabs.addTab(mission.get_widget(), "Mission")
        self.tabs.addTab(solve.get_widget(), "Solve")

        self.setCentralWidget(self.tabs)
        self.resize(1280, 720)

        # Create the theme switch widget
        # self.theme_switch = ThemeSwitch()


    def on_tab_change(self, index: int):
        if index != 2:
            return
        
        current_frame = self.tabs.currentWidget()
        assert isinstance(current_frame, AircraftConfigsWidget)
        
        current_frame.update_layout()


app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec())
