
"""RCAIDE GUI entry point and experience-mode coordinator.

Advanced Mode and Learner Mode use separate tab containers. Switching modes
temporarily swaps the active RCAIDE workspace so learner simplifications do not
overwrite an advanced aircraft that was already being edited.
"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QStackedWidget, QFileDialog, QMessageBox
from PyQt6.QtGui import QAction, QActionGroup, QIcon
from PyQt6.QtCore import QFileInfo
from qt_material import apply_stylesheet
import rcaide_io
from tabs import *
from tabs.visualize_geometry import visualize_geometry
from utilities import APP_DATA

import sys
import os
from copy import deepcopy

_IMG = os.path.join(APP_DATA, "images")

# Canonical orders are kept here so the standard Advanced Mode interface stays
# stable while Learner Mode exposes only its shorter guided workflow.
ADVANCED_TAB_NAMES = (
    "Home", "Vehicle Setup", "Visualize Geometry", "Configurations",
    "Analyses Setup", "Mission Setup", "Performance", "Run Mission",
    "Results Viewer",
)

LEARNER_TAB_NAMES = (
    "Learner Setup", "Visualize Geometry", "How Planes Fly",
    "Mission Setup", "Run Mission",
)

# Save these shared RCAIDE objects before entering Learner Mode, then restore
# the same object identities when returning to Advanced Mode.
ADVANCED_STATE_FIELDS = (
    "rcaide_vehicle", "propulsor_names", "vehicle", "current_file_path",
    "config_data", "rcaide_configs", "analysis_data", "rcaide_analyses",
    "mission_data", "rcaide_mission", "rcaide_results",
    "last_performance_result", "last_performance_label",
)

if sys.platform == "win32":
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LEADS.RCAIDE.GUI")

class App(QMainWindow):
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

        mode_menu = menubar.addMenu("Mode")
        self.advanced_mode_action = QAction("Advanced Mode", self, checkable=True)
        self.learner_mode_action = QAction("Learner Mode", self, checkable=True)
        mode_group = QActionGroup(self)
        mode_group.setExclusive(True)
        mode_group.addAction(self.advanced_mode_action)
        mode_group.addAction(self.learner_mode_action)
        self.advanced_mode_action.setChecked(True)
        mode_menu.addAction(self.learner_mode_action)
        mode_menu.addAction(self.advanced_mode_action)

        # Separate tab containers preserve each mode's widgets, selected tab,
        # and interface order instead of rebuilding one tab bar on every switch.
        self.advanced_tabs = QTabWidget()
        self.learner_tabs = QTabWidget()
        for tabs_widget in (self.advanced_tabs, self.learner_tabs):
            tabs_widget.setTabPosition(QTabWidget.TabPosition.North)
            tabs_widget.currentChanged.connect(self.on_tab_change)

        self.advanced_widgets = [
            (home.get_widget(), "Home"),
            (geometry.get_widget(), "Vehicle Setup"),
            (visualize_geometry.get_widget(), "Visualize Geometry"),
            (configurations.get_widget(), "Configurations"),
            (analysis.get_widget(), "Analyses Setup"),
            (mission.get_widget(), "Mission Setup"),
            (performance.get_widget(), "Performance"),
            (run_mission.get_widget(), "Run Mission"),
            (results_viewer.get_widget(), "Results Viewer"),
        ]

        # These learner widgets simplify presentation but still build and solve
        # with the application's RCAIDE vehicle and mission pipeline.
        learner_widget = learner.get_widget()
        self.learner_widgets = [
            (learner_widget, "Learner Setup"),
            (visualize_geometry.get_widget(), "Visualize Geometry"),
            (learner.LearnFlightWidget(), "How Planes Fly"),
            (learner.LearnerMissionSetupWidget(), "Mission Setup"),
            (learner.LearnerSolveWidget(), "Run Mission"),
        ]

        for widget, name in self.advanced_widgets:
            self.advanced_tabs.addTab(widget, name)
        for widget, name in self.learner_widgets:
            self.learner_tabs.addTab(widget, name)

        # Only one full tab bar is visible.  self.tabs and self.widgets remain
        # aliases for older methods that operate on the active experience.
        self.tab_stack = QStackedWidget()
        self.tab_stack.addWidget(self.advanced_tabs)
        self.tab_stack.addWidget(self.learner_tabs)
        self.tabs = self.advanced_tabs
        self.widgets = self.advanced_widgets
        self._advanced_tab_index = 0
        self._learner_tab_index = 0
        self._advanced_state = None

        learner_widget.setup_saved.connect(self._refresh_after_learner_save)
        self.learner_mode_action.triggered.connect(
            lambda: self.set_experience_mode("learner")
        )
        self.advanced_mode_action.triggered.connect(
            lambda: self.set_experience_mode("advanced")
        )
        self.experience_mode = "advanced"
        self.tab_stack.setCurrentWidget(self.advanced_tabs)

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.shutdown_vtk)

        self.setCentralWidget(self.tab_stack)
        screen = QApplication.primaryScreen()
        if screen:
            ag = screen.availableGeometry()
            self.resize(min(1280, ag.width()), min(ag.height() - 30, 836))
        else:
            self.resize(1280, 836)
        self.setMinimumSize(700, 480)

    def on_tab_change(self, index: int):
        """Refresh the newly selected tab only when its tab bar is visible."""
        tabs_widget = self.sender()
        if not isinstance(tabs_widget, QTabWidget):
            tabs_widget = self.tabs
        if hasattr(self, "tab_stack") and tabs_widget is not self.tab_stack.currentWidget():
            return
        current_frame = tabs_widget.currentWidget()
        if current_frame is None:
            return
        assert isinstance(current_frame, TabWidget)

        current_frame.update_layout()

    def set_experience_mode(self, mode):
        """Switch isolated workspaces without leaking vehicle or tab state."""
        if mode not in {"learner", "advanced"}:
            return
        if mode == self.experience_mode:
            self.learner_mode_action.setChecked(mode == "learner")
            self.advanced_mode_action.setChecked(mode == "advanced")
            return

        if mode == "learner":
            # Preserve the live advanced workspace without serializing or
            # reconstructing its RCAIDE containers.
            self._advanced_tab_index = self.advanced_tabs.currentIndex()
            self._advanced_state = {
                field: getattr(rcaide_io, field)
                for field in ADVANCED_STATE_FIELDS
            }

            learner_data = deepcopy(
                getattr(rcaide_io, "learner_data", None) or learner.DEFAULT_LEARNER_DATA
            )
            # A saved learner design is rebuilt from its small input record. An
            # unsaved learner workspace intentionally contains no aircraft.
            if getattr(rcaide_io, "learner_vehicle_built", False):
                learner.apply_learner_setup(learner_data)
            else:
                learner.initialize_unbuilt_learner_workspace(learner_data)
            self.tabs = self.learner_tabs
            self.widgets = self.learner_widgets
            self.tab_stack.setCurrentWidget(self.learner_tabs)
            # Learner Mode is a linear workflow, so every entry begins at the
            # simplified aircraft setup.
            self._learner_tab_index = 0
            self.learner_tabs.setCurrentIndex(0)
            for widget, _ in self.learner_widgets:
                widget.load_from_values()
        else:
            # Keep learner inputs for the next visit, then restore every shared
            # RCAIDE object that belonged to Advanced Mode.
            self._learner_tab_index = self.learner_tabs.currentIndex()
            learner_data = deepcopy(getattr(rcaide_io, "learner_data", {}))
            learner_comparisons = deepcopy(
                getattr(rcaide_io, "learner_comparison_data", [])
            )
            if self._advanced_state is not None:
                for field, value in self._advanced_state.items():
                    setattr(rcaide_io, field, value)
            rcaide_io.learner_data = learner_data
            rcaide_io.learner_comparison_data = learner_comparisons
            self.tabs = self.advanced_tabs
            self.widgets = self.advanced_widgets
            self.tab_stack.setCurrentWidget(self.advanced_tabs)
            self.advanced_tabs.setCurrentIndex(self._advanced_tab_index)

        self.experience_mode = mode
        self.learner_mode_action.setChecked(mode == "learner")
        self.advanced_mode_action.setChecked(mode == "advanced")

    def _refresh_after_learner_save(self):
        """Refresh learner tools only; advanced RCAIDE widgets stay untouched."""
        for widget, name in self.learner_widgets:
            if name in {
                "How Planes Fly", "Visualize Geometry", "Mission Setup", "Run Mission",
            }:
                widget.load_from_values()

    def save_all(self):
        """Save the active workspace and include learner metadata only there."""
        for widget, name in self.widgets:
            assert isinstance(widget, TabWidget)

        json_data = rcaide_io.write_to_json(
            include_learner=self.experience_mode == "learner"
        )
        name      = QFileDialog.getSaveFileName(self, 'Save As', os.path.join(APP_DATA, "aircraft"), "JSON (*.json)")[0]

        if not name:
            return
        if not QFileInfo(name).suffix():
            name += ".json"

        with open(name, 'w') as f:
            f.write(json_data)
        rcaide_io.current_file_path = name

    def load_all(self):
        name = QFileDialog.getOpenFileName(self, 'Open File', os.path.join(APP_DATA, "aircraft"), "JSON (*.json)")[0]
        if not name:
            return
        self.load_file(name)

    def load_file(self, path):
        try:
            with open(path, 'r') as f:
                data_str = f.read()
        except (FileNotFoundError, OSError):
            return
        rcaide_io.current_file_path = path
        rcaide_io.read_from_json(data_str, source_dir=os.path.dirname(os.path.abspath(path)))
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
        # Rebuild the mutable advanced geometry tree after a load so components
        # from the previous file are not appended to the newly loaded aircraft.
        # The fixed learner form can refresh safely without reconstruction.
        for i, (widget, tab_name) in enumerate(self.widgets):
            if tab_name == "Vehicle Setup" and self.experience_mode == "advanced":
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
        """Open the visualization tab for the currently active experience."""
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
        # Both containers stay alive in the stack, so hidden VTK views need the
        # same explicit cleanup as views in the currently visible mode.
        for widget, _ in self.advanced_widgets + self.learner_widgets:
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
    if sys.platform.startswith("linux"):
        import ctypes.util
        if ctypes.util.find_library("EGL") is None:
            print(
                "Error: libEGL is not installed. PyQt6 requires it on Linux.\n"
                "Install it with:  sudo apt install libegl1\n"
                "(or the equivalent package for your distribution)",
                file=sys.stderr,
            )
            sys.exit(1)

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
    apply_stylesheet(app, theme=os.path.join(APP_DATA, "style_sheets", "rcaide_dark_theme.xml"), extra=extra)
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
