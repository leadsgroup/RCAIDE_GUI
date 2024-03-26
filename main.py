import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from tabs.analysis import analysis
from tabs.geometry import geometry
from tabs.home import home
from tabs.mission import mission
from tabs.solve import solve

from widgets.theme import ThemeSwitch

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RCAIDE")

        layout = QGridLayout()
        self.setLayout(layout)
        
        menubar = self.menuBar()
    
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New")
        file_menu.addAction("Open")
        file_menu.addAction("Save")
        file_menu.addSeparator()
    
        # Theme submenu
        theme_menu = file_menu.addMenu("Theme")
        theme_menu.addAction("Light Theme").triggered.connect(ThemeSwitch.light_theme)
        theme_menu.addAction("Dark Theme").triggered.connect(ThemeSwitch.dark_theme)

                
        file_menu.addSeparator()
        file_menu.addAction("Quit")
    
        # Other menus
        menubar.addMenu("Edit")
        menubar.addMenu("View")
        menubar.addMenu("Help")
        
        # add textbox
        tbox = QPlainTextEdit()
        layout.addWidget(tbox, 1, 0)        

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setMovable(True)

        tabs.addTab(home.get_widget(), "Home")
        tabs.addTab(geometry.get_widget(), "Geometry")
        tabs.addTab(analysis.get_widget(), "Analysis")
        tabs.addTab(mission.get_widget(), "Mission")
        tabs.addTab(solve.get_widget(), "Solve")

        self.setCentralWidget(tabs)
        self.resize(800, 450)

        # Create the theme switch widget
        self.theme_switch = ThemeSwitch()
        



app = QApplication(sys.argv)

window = App()
window.show()

sys.exit(app.exec())

