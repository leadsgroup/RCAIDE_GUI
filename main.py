
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QFileDialog
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QFileInfo
from qt_material import apply_stylesheet
import rcaide_io
from tabs import *
from tabs.visualize_geometry import visualize_geometry

import sys
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
_IMG  = os.path.join(_ROOT, "app_data", "images")

if sys.platform == "win32":
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LEADS.RCAIDE.GUI")

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RCAIDE GUI")
        self.setWindowIcon(QIcon(os.path.join(_IMG, "logo.png")))

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

        self.tabs.currentChanged.connect(self.on_tab_change)

        self.widgets = []
        self.widgets.append((home.get_widget(), "Home"))
        self.widgets.append((geometry.get_widget(), "Vehicle Setup"))
        self.widgets.append((visualize_geometry.get_widget(), "Geometry Visualization"))
        self.widgets.append((aircraft_configs.get_widget(), "Configurations Setup"))
        self.widgets.append((analysis.get_widget(), "Analyses Setup"))
        self.widgets.append((mission.get_widget(), "Mission Setup"))
        self.widgets.append((solve.get_widget(), "Mission Simulation"))
        # Results Viewer reads the last mission.evaluate() output stored in rcaide_io.rcaide_results.
        self.widgets.append((results_viewer.get_widget(), "Results Viewer"))
        # self.widgets.append((shared_analysis_widget, "Multidisciplinary Analyses"))

        for widget, name in self.widgets:
            self.tabs.addTab(widget, name)

        self.setCentralWidget(self.tabs)
        screen = QApplication.primaryScreen()
        if screen:
            ag = screen.availableGeometry()
            self.resize(min(1280, ag.width()), min(ag.height() - 30, 836))
        else:
            self.resize(1280, 836)
        self.setMinimumSize(700, 480)

    def on_tab_change(self, index: int):
        current_frame = self.tabs.currentWidget()
        assert isinstance(current_frame, TabWidget)

        current_frame.update_layout()

    def save_all(self):
        for widget, name in self.widgets:
            assert isinstance(widget, TabWidget)

        json_data = rcaide_io.write_to_json()
        name      = QFileDialog.getSaveFileName(self, 'Save As', os.path.join(_ROOT, "app_data", "aircraft"), "JSON (*.json)")[0]

        if not name:
            return
        if not QFileInfo(name).suffix():
            name += ".json"

        with open(name, 'w') as f:
            f.write(json_data)
        rcaide_io.current_file_path = name

    def load_all(self):
        name = QFileDialog.getOpenFileName(self, 'Open File', os.path.join(_ROOT, "app_data", "aircraft"), "JSON (*.json)")[0]

        try:
            file = open(name, 'r')
        except FileNotFoundError:
            return

        data_str = file.read()
        file.close()
        rcaide_io.current_file_path = name
        rcaide_io.read_from_json(data_str, source_dir=os.path.dirname(os.path.abspath(name)))
        # Recreate geometry tab on each load so the component tree doesn't append duplicates across reloads
        for i, (widget, tab_name) in enumerate(self.widgets):
            if tab_name == "Vehicle Setup":
                # Keep the loaded geometry data before rebuilding the widget
                loaded_geometry = rcaide_io.rcaide_vehicle
                loaded_vehicle = rcaide_io.vehicle
                # Remembers which tab the user was on
                current_index = self.tabs.currentIndex()
                # Remove the old Geometry tab (it holds duplicated UI state)
                self.tabs.removeTab(i)
                # Create a fresh Geometry widget
                new_widget = geometry.get_widget()
                # Restore the loaded geometry data for load_from_values()
                rcaide_io.rcaide_vehicle = loaded_geometry
                rcaide_io.vehicle = loaded_vehicle
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
        self._go_to_geometry_visualization_tab()

    def _go_to_geometry_visualization_tab(self):
        for index in range(self.tabs.count()):
            if self.tabs.tabText(index).strip().lower() == "geometry visualization":
                self.tabs.setCurrentIndex(index)
                current_widget = self.tabs.widget(index)
                if isinstance(current_widget, TabWidget):
                    current_widget.update_layout()
                return

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(_IMG, "logo.png")))
    window = App()
    extra = {
        'density_scale': '-2',
        'delete': '#b0220c',
        'save': '#0291de',
        'menubar': '#021a32',
        'font_size': '15px'
    }
    apply_stylesheet(app, theme=os.path.join(_ROOT, "app_data", "style_sheets", "rcaide_dark_theme.xml"), extra=extra)
    custom_qss = app.styleSheet() + """
        QPushButton {
            border: 1px solid;
            border-radius: 4px;
            border-color: #ffffff;
        }
    """
    app.setStyleSheet(custom_qss)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
