
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QFileDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QFileInfo 

import values
from tabs import *
from tabs.visualize_geometry import visualize_geometry

import sys
import os 

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
        self.widgets.append((geometry.get_widget(), "Geometry Parameterization")) 
        self.widgets.append((visualize_geometry.get_widget(), "Geometry Visualization"))
        self.widgets.append((aircraft_configs.get_widget(), "Aircraft Configurations"))
        # make one shared analysis widget for both tabs
        shared_analysis_widget = analysis.get_widget() 
        self.widgets.append((mission.get_widget(shared_analysis_widget), "Mission Specification")) 
        self.widgets.append((shared_analysis_widget, "Aircraft Performance")) 

        self.widgets.append((solve.get_widget(), "Flight Simulation"))

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
        separator = os.path.sep
        name      = QFileDialog.getSaveFileName(self, 'Save File', "app_data" + separator + "aircraft" + separator, "JSON (*.json)")[0]
        
        # Check if name has suffix, append if necessary
        if not QFileInfo(name).suffix():
            name += ".json"
        
        file = open(name,'w')
        file.write(json_data)
        file.close()
    
    def load_all(self):
        separator = os.path.sep
        name      = QFileDialog.getOpenFileName(self, 'Open File', "app_data" + separator + "aircraft" + separator, "JSON (*.json)")[0]
        
        try:
            file = open(name, 'r')
        except FileNotFoundError:
            return
        
        data_str = file.read()
        file.close()
        values.read_from_json(data_str)
        # Recreate geometry tab on each load so the component tree doesn't append duplicates across reloads
        for i, (widget, tab_name) in enumerate(self.widgets):
            if tab_name == "Geometry Parameterization":
                # Keep the loaded geometry data before rebuilding the widget
                loaded_geometry = values.geometry_data
                # Remembers which tab the user was on
                current_index = self.tabs.currentIndex()
                # Remove the old Geometry tab (it holds duplicated UI state)
                self.tabs.removeTab(i)
                # Create a fresh Geometry widget
                new_widget = geometry.get_widget()
                # Restore the loaded geometry data for load_from_values()
                values.geometry_data = loaded_geometry
                # Insert the fresh tab back into the same position
                self.tabs.insertTab(i, new_widget, tab_name)
                # Update our cached widgets list.
                self.widgets[i] = (new_widget, tab_name)
                # Put the user back on the same tab if they were on Geometry
                if current_index == i:
                    self.tabs.setCurrentIndex(i)
                break
        for widget, name in self.widgets:
            assert isinstance(widget, TabWidget)
            widget.load_from_values()

app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec())
