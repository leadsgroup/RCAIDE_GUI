import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QFileDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QFileInfo
import qdarktheme

import values
from tabs import *
from tabs.visualize_geometry import visualize_geometry


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
        
        load_action = QAction("Load", self)
        load_action.triggered.connect(self.load_all)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_all)

        file_menu.addAction(load_action)
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

        self.widgets.append((visualize_geometry.get_widget(), "Visualize Geometry"))
        self.widgets.append((aircraft_configs.get_widget(), "Aircraft Configurations"))
        # make one shared analysis widget for both tabs
        shared_analysis_widget = analysis.get_widget()

        # add it as its own tab
        self.widgets.append((shared_analysis_widget, "Analysis"))

        # give Mission tab the same one
        self.widgets.append((mission.get_widget(shared_analysis_widget), "Mission"))

        self.widgets.append((solve.get_widget(), "Solve"))

        for widget, name in self.widgets:
            self.tabs.addTab(widget, name)

        self.setCentralWidget(self.tabs)
        self.resize(1280, 720)

        # name = "app_data/aircraft/737.json"
        # try:
        #     file = open(name, 'r')
        # except FileNotFoundError:
        #     print("Not found?")

        # data_str = file.read()
        # file.close()
        # values.read_from_json(data_str)
        # for widget, name in self.widgets:
        #     assert isinstance(widget, TabWidget)
        #     widget.load_from_values()

    def on_tab_change(self, index: int):
        current_frame = self.tabs.currentWidget()
        assert isinstance(current_frame, TabWidget)

        current_frame.update_layout()

    def save_all(self):
        for widget, name in self.widgets:
            assert isinstance(widget, TabWidget)
            # widget.save_to_values()
          
        json_data = values.write_to_json()
        name = QFileDialog.getSaveFileName(self, 'Save File', "app_data/aircraft/", "JSON (*.json)")[0]
        
        # Check if name has suffix, append if necessary
        if not QFileInfo(name).suffix():
            name += ".json"
        
        file = open(name,'w')
        file.write(json_data)
        file.close()
    
    def load_all(self):
        name = QFileDialog.getOpenFileName(self, 'Open File', "app_data/aircraft/", "JSON (*.json)")[0]
        
        try:
            file = open(name, 'r')
        except FileNotFoundError:
            return
        
        data_str = file.read()
        file.close()
        values.read_from_json(data_str)
        for widget, name in self.widgets:
            assert isinstance(widget, TabWidget)
            widget.load_from_values()


app = QApplication(sys.argv)
qdarktheme.setup_theme()
window = App()
window.show()
sys.exit(app.exec())
