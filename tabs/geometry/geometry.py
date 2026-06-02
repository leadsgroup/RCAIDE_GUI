# RCAIDE_GUI/tabs/geometry/geometry.py

# RCAIDE imports
import RCAIDE

# RCAIDE-GUI imports
from tabs.visualize_geometry.core_3d_viewer import Core3DViewer
from tabs.geometry.frames import *
from tabs import TabWidget
from tabs.visualize_geometry.visualize_geometry import VisualizeGeometryWidget
from utilities import set_data
import rcaide_io

# PyQt imports
from PyQt6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QTimer
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QStackedLayout, QTreeWidget, QTreeWidgetItem, \
    QLabel, QLineEdit, QApplication

# Python imports
from typing import Type
import vtk
import os

# Maps geometry tab name → rcaide_io.vehicle container attribute name.
_TAB_TO_CONTAINER = {
    "Booms":        "booms",
    "Cargo Bays":   "cargo_bays",
    "Fuselages":    "fuselages",
    "Landing Gear": "landing_gears",
    "Wings":        "wings",
}

# ------------------------------------------------------------------------------
# Geometry Widget
# ------------------------------------------------------------------------------
class GeometryWidget(TabWidget):
    def __init__(self):
        """Create a widget for entering vehicle geometry."""
        super(GeometryWidget, self).__init__()

        # Define actions based on the selected index
        self.frames: list[Type[GeometryFrame]] = [VehicleFrame, BoomFrame, CargoBayFrame, FuselageFrame, LandingGearFrame,
                                                  PowertrainFrame, WingsFrame]
        self.tabs = ["", "Booms", "Cargo Bays", "Fuselages","Landing Gear" , "Powertrain", "Wings"]

        options = ["Add Vehicle Component", "Add Boom", "Add Cargo Bay", "Add Fuselage", "Add Landing Gear" , "Add Powertrain", "Add Wing"]

        rcaide_io.rcaide_vehicle = rcaide_io.new_rcaide_vehicle_data()
        rcaide_io.vehicle = RCAIDE.Vehicle()

        base_layout = QHBoxLayout()
        self.tree_frame_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        self.main_layout = QStackedLayout()
        # Gate preview redraws during bulk operations (e.g., load from file).
        self._preview_updates_enabled = True
        # Ensure VTK cleanup runs only once during shutdown.
        self._preview_cleaned_up = False

        for index, frame in enumerate(self.frames):
            frame_widget = frame()
            frame_widget.set_save_function(self.save_data)
            frame_widget.set_tab_index(index)
            self.main_layout.addWidget(frame_widget)

        vehicle_name_layout = QHBoxLayout()
        vehicle_name_layout.addWidget(QLabel("Vehicle Name:"))
        self.vehicle_name_input = QLineEdit()
        vehicle_name_layout.addWidget(self.vehicle_name_input)
        self.tree_frame_layout.addLayout(vehicle_name_layout)

        self.dropdown = QComboBox()
        self.dropdown.addItems(options)
        self.dropdown.currentIndexChanged.connect(self.on_dropdown_change)
        self.tree_frame_layout.addWidget(self.dropdown)

        # Create a QComboBox and add options
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Component Tree"])
        self.tree.itemClicked.connect(self.on_tree_item_clicked)

        vehicle_item = QTreeWidgetItem(["Vehicle"])
        self.tree.addTopLevelItem(vehicle_item)
        self.tree_frame_layout.addWidget(self.tree)
        self.tree.expandAll()

        # Reuse the full Geometry Visualization widget as an embedded preview.
        self.preview_widget = VisualizeGeometryWidget(show_lopa=False, show_fuel_tanks=False, show_cargo_bays=False)
        # Hide advanced controls in Vehicle Setup; keep only the 3D viewport.
        if hasattr(self.preview_widget, "toolbar"):
            self.preview_widget.toolbar.hide()
        if hasattr(self.preview_widget, "colorbar_widget") and self.preview_widget.colorbar_widget:
            self.preview_widget.colorbar_widget.hide()
        self.preview_widget.setMinimumHeight(180)

        # Wrap preview in a titled box so users can identify it clearly.
        self.preview_container = QWidget()
        self.preview_container.setObjectName("aircraftPreviewContainer")
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(6, 6, 6, 6)
        preview_layout.setSpacing(6)
        self.preview_container.setLayout(preview_layout)
        # Added label to preview container
        self.preview_label = QLabel("Aircraft Preview")
        self.preview_label.setObjectName("aircraftPreviewLabel")
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_widget, 1)
        # Style the preview container and label for better visual separation and clarity.
        self.preview_container.setStyleSheet("""
            QLabel#aircraftPreviewLabel {
                border: none;
                font-weight: 600;
            }
        """)
        # Keep preview compact by default and widen it on hover without re-parenting.
        self._preview_hovered = False
        self._preview_base_width = 300
        self._preview_hover_width = 660
        self.preview_container.setMinimumWidth(self._preview_base_width)
        self.preview_container.setMaximumWidth(self._preview_hover_width)
        self.preview_container.setMaximumHeight(300)
        self._preview_width_anim = QPropertyAnimation(self.preview_container, b"minimumWidth", self)
        self._preview_width_anim.setDuration(160)
        self._preview_width_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.preview_container.installEventFilter(self)
        self.preview_widget.installEventFilter(self)
        if hasattr(self.preview_widget, "vtkWidget"):
            self.preview_widget.vtkWidget.installEventFilter(self)

        self.tree_frame_layout.addWidget(self.preview_container, 1)
        app = QApplication.instance()
        if app is not None:
            # Fallback cleanup hook in case closeEvent order differs by platform.
            app.aboutToQuit.connect(self._cleanup_preview)

        self.right_layout.addLayout(self.main_layout)
        base_layout.addLayout(self.tree_frame_layout, 1)
        base_layout.addLayout(self.right_layout, 4)

        self.main_layout.setSpacing(3)
        base_layout.setSpacing(3)

        # Initially display the DefaultFrame
        self.main_layout.setCurrentIndex(0)
        self.setLayout(base_layout)

    def on_dropdown_change(self, index):
        """Change the index of the main layout based on the selected index of the dropdown.

        Args:
            index: The index of the selected item in the dropdown.
        """
        layout = self.layout()
        if layout:
            self.main_layout.setCurrentIndex(index)

            # call update_layout method of the selected frame
            frame = self.main_layout.currentWidget()
            assert isinstance(frame, GeometryFrame)
            frame.update_layout()

    def on_tree_item_clicked(self, item: QTreeWidgetItem, _col):
        """Change the index of the main layout based on the selected item in the tree.

        Args:
            item: The selected item in the tree.
            _col: The column index of the selected item. (Not used)

        """
        assert item is not None
        # get item depth
        depth = 0

        item2: QTreeWidgetItem = item
        while item2.parent():
            parent = item2.parent()
            assert parent is not None

            item2 = parent
            depth += 1

        if depth == 0:
            self.main_layout.setCurrentIndex(0)
            self.main_layout.currentWidget().update_layout()
            return
        if depth == 1:
            top_item = item.parent()

            assert top_item is not None
            tree_index = top_item.indexOfChild(item)
            tab_index = self.find_tab_index(tree_index)

            self.main_layout.setCurrentIndex(tab_index)
        if depth == 2:
            component_item = item.parent()

            assert component_item is not None
            top_item = component_item.parent()
            assert top_item is not None

            tree_index = top_item.indexOfChild(component_item)
            tab_index = self.find_tab_index(tree_index)
            self.main_layout.setCurrentIndex(tab_index)

            index = component_item.indexOfChild(item)
            frame = self.main_layout.currentWidget()
            assert isinstance(frame, GeometryFrame)
            frame.load_data(rcaide_io.rcaide_vehicle[tab_index][index], index)

    def save_data(self, tab_index, tree_index=-1, vehicle_component=None, index=-1, data=None, new=False, persist=False):
        """Save the entered data in a frame to the list.

        Args:
            tab_index: The index of the tab.
            tree_index: The index of the tab in the tree.
            index: The index of the vehicle element in the list. (Within its type, eg fuselage #0, #1, etc.)
            vehicle_component: The vehicle component to be appended to the vehicle.
            data: The data to be saved.
            new: A flag to indicate if the data is of a new element.
            persist: When True, write the updated data back to the currently loaded JSON file.
        """
        if data is None:
            return

        assert tab_index >= 0
        if tab_index == 0:
            rcaide_io.rcaide_vehicle[0] = data
            rcaide_io.vehicle.tag = data["name"]
            for data_unit_label in VehicleFrame.data_units_labels:
                rcaide_label = data_unit_label[-1]
                user_label   = data_unit_label[0]
                set_data(rcaide_io.vehicle, rcaide_label, data[user_label][0])
        else:
            top_item = self.tree.topLevelItem(0)
            assert top_item is not None
            category_name = self.tabs[tab_index]
            component_item = None
            for i in range(top_item.childCount()):
                child = top_item.child(i)
                if child.text(0) == category_name:
                    component_item = child
                    break
            if component_item is None:
                component_item = QTreeWidgetItem([category_name])
                component_item.setExpanded(True)
                insert_index = 0
                for i in range(1, tab_index):
                    if rcaide_io.rcaide_vehicle[i]:
                        insert_index += 1
                top_item.insertChild(insert_index, component_item)

            if new:
                if index == -1:
                    rcaide_io.rcaide_vehicle[tab_index].append(data)
                else:
                    frame : GeometryFrame = self.frames[tab_index]()
                    frame.load_data(data, -1)
                    vehicle_component = frame.create_rcaide_structure()
                    frame.deleteLater()

                child = QTreeWidgetItem([data["name"]])
                component_item.addChild(child)
                child.setSelected(True)
                index = component_item.indexOfChild(child)
            else:
                rcaide_io.rcaide_vehicle[tab_index][index] = data
                if tree_index == -1:
                    tree_index = index
                child = component_item.child(tree_index)
                if child:
                    child.setText(0, data["name"])

                # Rebuild the RCAIDE component so run_solve sees the updated values.
                # (vehicle_component is None on updates — append_component is not called,
                # so we must replace the existing entry directly.)
                container_key = _TAB_TO_CONTAINER.get(category_name)
                if container_key and tab_index != 5:
                    container = getattr(rcaide_io.vehicle, container_key, None)
                    if container is not None:
                        keys = list(container.keys())
                        if index < len(keys):
                            tmp = self.frames[tab_index]()
                            tmp.load_data(data, index)
                            container[keys[index]] = tmp.create_rcaide_structure()
                            tmp.deleteLater()

        if vehicle_component:
            if tab_index == 5:
                rcaide_io.vehicle.append_energy_network(vehicle_component)
            else:
                rcaide_io.vehicle.append_component(vehicle_component)

        # Keep preview synced with current geometry edits.
        if self._preview_updates_enabled:
            self.preview_widget.run_solve()

        # Write changes back to the loaded file when explicitly requested.
        if persist and getattr(rcaide_io, "current_file_path", ""):
            try:
                json_data = rcaide_io.write_to_json()
                with open(rcaide_io.current_file_path, "w") as f:
                    f.write(json_data)
            except Exception as e:
                print(f"Auto-save to file failed: {e}")

        self.tree.expandAll()

        return index

    def load_from_values(self):
        """Load the geometry data from the values file."""
        if not isinstance(rcaide_io.rcaide_vehicle, list):
            tag = getattr(rcaide_io.vehicle, "tag", "")
            self.vehicle_name_input.setText(str(tag))
            self.preview_widget.run_solve()
            return

        # Avoid repeated expensive redraws while reconstructing full geometry tree.
        self._preview_updates_enabled = False
        self.tree.clear()
        vehicle_item = QTreeWidgetItem(["Vehicle"])
        self.tree.addTopLevelItem(vehicle_item)

        if rcaide_io.rcaide_vehicle:
            # Load vehicle data (index 0) - it's already in UI format
            if rcaide_io.rcaide_vehicle[0]:
                vehicle_data = rcaide_io.rcaide_vehicle[0]
                self.vehicle_name_input.setText(vehicle_data.get("name", ""))
                # Update the vehicle frame
                frame = self.main_layout.widget(0)
                if isinstance(frame, GeometryFrame):
                    frame.load_data(vehicle_data, 0)

            # Build the component tree directly from the loaded values structure
            for tab_index, data_list in enumerate(rcaide_io.rcaide_vehicle):
                if tab_index == 0 or not data_list:
                    continue

                category_name = self.tabs[tab_index]
                component_item = QTreeWidgetItem([category_name])
                component_item.setExpanded(True)
                vehicle_item.addChild(component_item)

                for index, data in enumerate(data_list):
                    child = QTreeWidgetItem([data.get("name", f"Item {index}")])
                    component_item.addChild(child)

        self._preview_updates_enabled = True
        # Single redraw after all loaded parts are in place.
        self.preview_widget.run_solve()
        self.tree.expandAll()

    def update_layout(self):
        # Refresh preview when this tab becomes active.
        self.preview_widget.run_solve()

    def eventFilter(self, watched, event):
        watched_preview = watched in {
            self.preview_container,
            self.preview_widget,
            getattr(self.preview_widget, "vtkWidget", None),
        }
        if watched_preview:
            if event.type() == QEvent.Type.Enter:
                self._set_preview_hover_state(True)
            elif event.type() == QEvent.Type.Leave:
                # Delay so transitions between child widgets don't collapse immediately.
                QTimer.singleShot(0, self._sync_preview_hover_state)
        return super().eventFilter(watched, event)

    def _sync_preview_hover_state(self):
        vtk_widget = getattr(self.preview_widget, "vtkWidget", None)
        hovered = (
            self.preview_container.underMouse()
            or self.preview_widget.underMouse()
            or (vtk_widget.underMouse() if vtk_widget else False)
        )
        self._set_preview_hover_state(hovered)

    def _set_preview_hover_state(self, hovered: bool):
        if self._preview_hovered == hovered:
            return
        self._preview_hovered = hovered
        target = self._preview_hover_width if hovered else self._preview_base_width
        self._preview_width_anim.stop()
        self._preview_width_anim.setStartValue(self.preview_container.minimumWidth())
        self._preview_width_anim.setEndValue(target)
        self._preview_width_anim.start()

    def closeEvent(self, event):
        # Clean embedded VTK resources before QWidget teardown.
        self._cleanup_preview()
        super().closeEvent(event)

    def _cleanup_preview(self):
        if self._preview_cleaned_up:
            return
        self._preview_cleaned_up = True
        self._preview_updates_enabled = False

        try:
            # Suppress VTK warnings during teardown path.
            vtk.vtkObject.GlobalWarningDisplayOff()
            if hasattr(self, "preview_widget") and self.preview_widget:
                # Hide first, then release GL/VTK resources.
                self.preview_widget.hide()
                self.preview_widget.vtkWidget.hide()
                rw = self.preview_widget.vtkWidget.GetRenderWindow()
                iren = rw.GetInteractor() if rw else None
                if iren:
                    # Stop interactor loop before finalizing the window.
                    iren.TerminateApp()
                if rw:
                    # Finalize render window explicitly to avoid Win32 handle errors.
                    rw.SetOffScreenRendering(1)
                    rw.Finalize()
        except Exception:
            # Ignore teardown errors to keep app shutdown clean.
            pass

    # noinspection PyMethodMayBeStatic
    def find_tree_index(self, tab_index):
        # Start from tab_index - 1 to account for rcaide_io.rcaide_vehicle[0] being None
        tree_index = tab_index - 1
        # Start from 1 to skip rcaide_io.rcaide_vehicle[0]
        for i in range(1, tab_index):
            if not rcaide_io.rcaide_vehicle[i]:
                tree_index -= 1

        tree_index = max(0, tree_index)
        return tree_index

    # noinspection PyMethodMayBeStatic
    def find_tab_index(self, tree_index):
        tab_index = 0
        count = 0

        # Start from 1 to skip rcaide_io.rcaide_vehicle[0]
        for i in range(1, len(rcaide_io.rcaide_vehicle)):
            if not rcaide_io.rcaide_vehicle[i]:
                continue
            count += 1
            if count == tree_index + 1:
                tab_index = i
                break
        return tab_index


def get_widget() -> QWidget:
    """Return the geometry widget.

    Returns:
        The geometry widget.
    """
    return GeometryWidget()
