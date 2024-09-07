import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtGui import QAction
import qdarktheme

from tabs import *


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RCAIDE GUI")

        menubar = self.menuBar()
        if menubar is None:
            return

        # File menu
        file_menu = menubar.addMenu("File")
        if file_menu is None:
            return
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_all)

        file_menu.addAction("New")
        file_menu.addAction("Open")
        file_menu.addAction(save_action)
        file_menu.addSeparator()

        file_menu.addSeparator()
        file_menu.addAction("Quit")

        menubar.addMenu("Documentation")

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        # self.tabs.setMovable(True)

        self.tabs.currentChanged.connect(self.on_tab_change)
        
        self.widgets = []
        self.widgets.append((home.get_widget(), "Home"))
        self.widgets.append((geometry.get_widget(), "Geometry"))
        self.widgets.append((TabWidget(), "Visualize Geometry"))
        self.widgets.append((aircraft_configs.get_widget(), "Aircraft Configurations"))
        self.widgets.append((analysis.get_widget(), "Analysis"))
        self.widgets.append((mission.get_widget(), "Mission"))
        self.widgets.append((solve.get_widget(), "Solve"))

        for widget, name in self.widgets:
            self.tabs.addTab(widget, name)
        
        self.setCentralWidget(self.tabs)
        self.resize(1280, 720)

        # Create the theme switch widget
        # self.theme_switch = ThemeSwitch()

    def on_tab_change(self, index: int):
        current_frame = self.tabs.currentWidget()
        assert isinstance(current_frame, TabWidget)

        current_frame.update_layout()
    
    def save_all(self):
        print("Save All!")


app = QApplication(sys.argv)
qdarktheme.setup_theme()
window = App()
window.show()
sys.exit(app.exec())
