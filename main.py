"""RCAIDE desktop entry point, including the native AI assistant drawer."""

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QFileDialog, QMessageBox
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QAbstractAnimation, QEasingCurve, QFileInfo, QPropertyAnimation, Qt
from qt_material import apply_stylesheet
import rcaide_io
# Starts the development API automatically and leaves hosted deployments alone.
from agent_service.bootstrap import start_local_agent_service, stop_local_agent_service
from tabs import *
from tabs.visualize_geometry import visualize_geometry
# These two widgets provide the floating launcher and right-side chat drawer.
from tabs.ai_assistant import AIAssistantButton, AIAssistantDock

import sys
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
_IMG  = os.path.join(_ROOT, "app_data", "images")

if sys.platform == "win32":
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LEADS.RCAIDE.GUI")

class App(QMainWindow):
    """Main RCAIDE window containing workflow tabs and the AI assistant drawer."""

    def __init__(self):
        super().__init__()
        self._vtk_shutdown = False

        self.setWindowTitle("RCAIDE GUI")
        self.setWindowIcon(QIcon(os.path.join(_IMG, "logo.png")))

        menubar = self.menuBar()
        if menubar is None:
            return

        # File menu
        file_menu = menubar.addMenu("File")
        if file_menu is None:
            return

        load_action = QAction("Open RCAIDE JSON...", self)
        load_action.triggered.connect(self.load_all)

        save_action = QAction("Save RCAIDE JSON...", self)
        save_action.triggered.connect(self.save_all)

        import_vsp_action = QAction("Import VSP...", self)
        import_vsp_action.triggered.connect(self.import_vsp)

        export_vsp_action = QAction("Export VSP...", self)
        export_vsp_action.triggered.connect(self.export_vsp)

        file_menu.addAction(load_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(import_vsp_action)
        file_menu.addAction(export_vsp_action)
        file_menu.addSeparator()
        quit_action = file_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)

        menubar.addMenu("Documentation")

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.tabs.currentChanged.connect(self.on_tab_change)

        self.widgets = []
        self.widgets.append((home.get_widget(), "Home"))
        self.widgets.append((geometry.get_widget(), "Vehicle Setup"))
        self.widgets.append((visualize_geometry.get_widget(), "Visualize Geometry"))
        self.widgets.append((configurations.get_widget(), "Configurations"))
        self.widgets.append((analysis.get_widget(), "Analyses Setup"))
        self.widgets.append((mission.get_widget(), "Mission Setup"))
        self.widgets.append((performance.get_widget(), "Performance"))
        self.widgets.append((run_mission.get_widget(), "Run Mission"))
        self.widgets.append((results_viewer.get_widget(), "Results Viewer"))

        for widget, name in self.widgets:
            self.tabs.addTab(widget, name)

        # The assistant is a compact in-app drawer, not a separate workflow tab.
        # Floating side handle keeps the assistant out of the workflow tab bar.
        self.ai_button = AIAssistantButton(self)
        # Reserve a narrow edge rail so the collapsed logo never covers controls.
        self.setContentsMargins(0, 0, AIAssistantButton.COLLAPSED_WIDTH + 12, 0)
        self.ai_button.raise_()
        self.ai_button.widthChanged.connect(self._position_ai_handle)

        self.ai_dock = AIAssistantDock(self)
        # QDockWidget lets the assistant share the application window while
        # preserving the existing tab-based engineering workflow.
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ai_dock)
        self.ai_dock.hide()
        # Keep the launcher and drawer state synchronized regardless of whether
        # visibility changes through the button, animation, or Qt itself.
        self.ai_button.clicked.connect(self.toggle_ai_assistant)
        self.ai_dock.visibilityChanged.connect(self._sync_ai_handle)

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.shutdown_vtk)

        self.setCentralWidget(self.tabs)
        screen = QApplication.primaryScreen()
        if screen:
            ag = screen.availableGeometry()
            self.resize(min(1280, ag.width()), min(ag.height() - 30, 836))
        else:
            self.resize(1280, 836)
        self.setMinimumSize(700, 480)

    def on_tab_change(self, index: int):
        """Refresh the selected workflow tab and visible assistant context."""
        current_frame = self.tabs.currentWidget()
        assert isinstance(current_frame, TabWidget)

        current_frame.update_layout()

        # The context label reports the newly active tab and current project state.
        if hasattr(self, "ai_dock") and self.ai_dock.isVisible():
            self.ai_dock.refresh_context_label()

    def toggle_ai_assistant(self):
        """Open or close the AI drawer without overlapping animations."""
        # Ignore repeated clicks while the previous transition is still running.
        if getattr(self, "_ai_drawer_animation", None) is not None:
            if self._ai_drawer_animation.state() == QAbstractAnimation.State.Running:
                return

        if self.ai_dock.isVisible():
            self._animate_ai_drawer(opening=False)
            return

        self.ai_button.play_launch_animation()
        self._animate_ai_drawer(opening=True)

    def _animate_ai_drawer(self, opening: bool):
        """Animate the drawer's maximum width to reveal or hide it."""
        # Give technical Markdown, tables, and long parameter paths enough room.
        # Scale with the main window while preserving the working canvas on laptops.
        target_width = max(500, min(620, int(self.width() * 0.32)))
        if opening:
            self.ai_dock.setMinimumWidth(0)
            self.ai_dock.setMaximumWidth(0)
            self.ai_dock.show()
            start_width, end_width = 0, target_width
        else:
            start_width, end_width = self.ai_dock.width(), 0
            self.ai_dock.setMinimumWidth(0)
            self.ai_dock.setMaximumWidth(max(start_width, target_width))

        # Animate maximumWidth because QMainWindow manages dock geometry itself.
        self.ai_dock.show()
        self.ai_dock.raise_()
        self.ai_button.set_expanded(opening)
        # Store the direction so the completion handler can set final constraints.
        self._ai_drawer_opening = opening
        self._ai_drawer_animation = QPropertyAnimation(self.ai_dock, b"maximumWidth", self)
        self._ai_drawer_animation.setDuration(360)
        self._ai_drawer_animation.setStartValue(start_width)
        self._ai_drawer_animation.setEndValue(end_width)
        self._ai_drawer_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._ai_drawer_animation.valueChanged.connect(lambda _value: self._position_ai_handle())
        self._ai_drawer_animation.finished.connect(self._finish_ai_drawer_animation)
        self._ai_drawer_animation.start()

    def _finish_ai_drawer_animation(self):
        """Restore normal dock constraints after the width transition."""
        if self._ai_drawer_opening:
            self.ai_dock.setMinimumWidth(480)
            self.ai_dock.setMaximumWidth(16777215)
            self.ai_dock.refresh_context_label()
        else:
            self.ai_dock.hide()
            self.ai_dock.setMinimumWidth(480)
            self.ai_dock.setMaximumWidth(16777215)
        self._sync_ai_handle(self.ai_dock.isVisible())

    def _sync_ai_handle(self, visible: bool):
        """Match the launcher appearance and position to drawer visibility."""
        self.ai_button.set_expanded(visible)
        self._position_ai_handle()

    def _position_ai_handle(self):
        """Anchor the floating launcher inside the reserved right-edge rail."""
        if not hasattr(self, "ai_button"):
            return
        # Keep the handle anchored inside its reserved rail. On hover, its label
        # grows leftward temporarily without moving the logo or relaying out tabs.
        x = max(0, self.width() - self.ai_button.width() - 7)
        y = max(
            self.menuBar().height() + 24,
            self.height() - self.ai_button.height() - 26,
        )
        self.ai_button.move(x, y)
        self.ai_button.raise_()

    def resizeEvent(self, event):
        # Re-anchor the launcher whenever the main window changes size.
        super().resizeEvent(event)
        self._position_ai_handle()

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
        self._refresh_gui_after_load()

    def import_vsp(self):
        try:
            import vsp  # noqa: F401
        except ImportError:
            try:
                import openvsp  # noqa: F401
            except ImportError:
                QMessageBox.warning(self, "OpenVSP Not Available",
                    "The openvsp Python package is not installed.\n"
                    "Install it with:  pip install openvsp")
                return

        from RCAIDE.Framework.External_Interfaces.OpenVSP.import_vsp_vehicle import import_vsp_vehicle

        path = QFileDialog.getOpenFileName(self, 'Import OpenVSP Model', '', "OpenVSP (*.vsp3)")[0]
        if not path:
            return

        try:
            imported_vehicle = import_vsp_vehicle(path)
        except Exception as exc:
            QMessageBox.critical(self, "VSP Import Failed", str(exc))
            return

        # Serialise through the same pipeline that read_from_json uses so all
        # type restoration and UI conversion runs identically to a normal load.
        import json as _json
        vehicle_dict = rcaide_io.make_json_safe(rcaide_io._build_dict_base_with_types(imported_vehicle))
        json_str = _json.dumps({
            "rcaide_vehicle": rcaide_io.add_default_unit_arguments(vehicle_dict),
            "config_data":    [],
            "analysis_data":  [],
            "mission_data":   [],
        })
        rcaide_io.read_from_json(json_str, source_dir=os.path.dirname(os.path.abspath(path)))
        self._refresh_gui_after_load()

    def export_vsp(self):
        try:
            import vsp  # noqa: F401
        except ImportError:
            try:
                import openvsp  # noqa: F401
            except ImportError:
                QMessageBox.warning(self, "OpenVSP Not Available",
                    "The openvsp Python package is not installed.\n"
                    "Install it with:  pip install openvsp")
                return

        from RCAIDE.Framework.External_Interfaces.OpenVSP.export_vsp_vehicle import export_vsp_vehicle

        path = QFileDialog.getSaveFileName(self, 'Export OpenVSP Model', '', "OpenVSP (*.vsp3)")[0]
        if not path:
            return

        tag = path[:-5] if path.endswith('.vsp3') else path

        try:
            export_vsp_vehicle(rcaide_io.vehicle, tag)
        except Exception as exc:
            QMessageBox.critical(self, "VSP Export Failed", str(exc))

    def _refresh_gui_after_load(self):
        # Recreate geometry tab on each load so the component tree doesn't append duplicates across reloads
        for i, (widget, tab_name) in enumerate(self.widgets):
            if tab_name == "Vehicle Setup":
                loaded_geometry = rcaide_io.rcaide_vehicle
                loaded_vehicle  = rcaide_io.vehicle
                current_index   = self.tabs.currentIndex()
                cleanup = getattr(widget, "_cleanup_preview", None)
                if callable(cleanup):
                    cleanup()
                self.tabs.removeTab(i)
                widget.deleteLater()
                new_widget = geometry.get_widget()
                rcaide_io.rcaide_vehicle = loaded_geometry
                rcaide_io.vehicle        = loaded_vehicle
                self.tabs.insertTab(i, new_widget, tab_name)
                self.widgets[i] = (new_widget, tab_name)
                if current_index == i:
                    self.tabs.setCurrentIndex(i)
                break
        for widget, name in self.widgets:
            assert isinstance(widget, TabWidget)
            widget.load_from_values()
        self._go_to_geometry_visualization_tab()

    def _go_to_geometry_visualization_tab(self):
        for index in range(self.tabs.count()):
            if self.tabs.tabText(index).strip().lower() == "visualize geometry":
                self.tabs.setCurrentIndex(index)
                current_widget = self.tabs.widget(index)
                if isinstance(current_widget, TabWidget):
                    current_widget.update_layout()
                return

    def shutdown_vtk(self):
        """Release every VTK context before Qt destroys native child windows."""
        if self._vtk_shutdown:
            return
        self._vtk_shutdown = True
        for widget, _ in self.widgets:
            cleanup = getattr(widget, "_cleanup_preview", None)
            if callable(cleanup):
                cleanup()
            shutdown = getattr(widget, "shutdown_vtk", None)
            if callable(shutdown):
                shutdown()

    def closeEvent(self, event):
        self.shutdown_vtk()
        super().closeEvent(event)

def main():
    """Create the Qt application, backend lifecycle, theme, and main window."""
    app = QApplication(sys.argv)
    # Development builds use a local backend; configured hosted URLs bypass it.
    local_agent_process = start_local_agent_service()
    # Stop only the backend process created for this application session.
    app.aboutToQuit.connect(lambda: stop_local_agent_service(local_agent_process))
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
