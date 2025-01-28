from typing import Type

import RCAIDE
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QHBoxLayout, QVBoxLayout, QComboBox, 
    QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from tabs.geometry.frames import *
from tabs import TabWidget
from utilities import set_data, create_line_bar
import values

class GeometryWidget(TabWidget):
    def __init__(self):
        super().__init__()
        self.main_window = GeometryMainWindow()
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.main_window)
        self.setLayout(layout)

class GeometryMainWindow(QMainWindow):
    def __init__(self):
        """Create a widget for entering vehicle geometry."""
        super().__init__()

        self.frames: list[Type[GeometryFrame]] = [
            VehicleFrame, FuselageFrame, WingsFrame, NacelleFrame, LandingGearFrame, EnergyNetworkFrame
        ]
        self.tabs = ["Vehicle", "Fuselages", "Wings", "Nacelles", "Landing Gear", "Energy Networks"]
        options = ["Set Vehicle Parameters", "Add Fuselage", "Add Wing", "Add Nacelle", "Add Landing Gear", "Add Energy Network"]

        values.geometry_data = [[] for _ in self.tabs]
        values.vehicle = RCAIDE.Vehicle()

        self.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks |
            QMainWindow.DockOption.AllowTabbedDocks |
            QMainWindow.DockOption.AnimatedDocks
        )

        self.create_tree_dock(options)
        self.create_content_dock()

    def create_tree_dock(self, options):
        """Create the left dock for the tree and dropdown."""
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)

        # Vehicle name input
        vehicle_name_layout = QHBoxLayout()
        vehicle_name_layout.addWidget(QLabel("Vehicle Name:"))
        self.vehicle_name_input = QLineEdit()
        vehicle_name_layout.addWidget(self.vehicle_name_input)
        tree_layout.addLayout(vehicle_name_layout)

        # Dropdown for component selection
        self.dropdown = QComboBox()
        self.dropdown.addItems(options)
        self.dropdown.currentIndexChanged.connect(self.on_dropdown_change)
        tree_layout.addWidget(self.dropdown)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Vehicle Components"])
        self.tree.itemClicked.connect(self.on_tree_item_clicked)

        # Add root tree item
        vehicle_item = QTreeWidgetItem(["Vehicle"])
        self.tree.addTopLevelItem(vehicle_item)
        tree_layout.addWidget(self.tree)

        # Create the dockable tree view
        self.tree_dock = QDockWidget("Vehicle Components", self)
        self.tree_dock.setObjectName("vehicle_components_dock")

        self.tree_dock.setWidget(tree_container)
        self.tree_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tree_dock)

    def create_content_dock(self):
        """Create the right dock for the content view."""
        content_container = QWidget()
        self.content_layout = QVBoxLayout(content_container)

        # Scroll area for component frames
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_widget = QWidget()

        self.component_layout = QVBoxLayout(self.scroll_widget)
        self.component_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.scroll_widget)

        self.component_frames = {}

        for index, frame_class in enumerate(self.frames):
            frame_widget = frame_class()
            frame_widget.set_save_function(self.save_data)
            frame_widget.set_tab_index(index)

            self.component_frames[index] = frame_widget

            if index == 0:  # Vehicle frame
                self.component_layout.addWidget(frame_widget)
                self.component_layout.addWidget(create_line_bar())
            else:
                frame_widget.hide()
                self.component_layout.addWidget(frame_widget)

        self.content_layout.addWidget(self.scroll_area)

        self.content_dock = QDockWidget("Component Details", self)
        self.content_dock.setObjectName("component_details_dock")

        self.content_dock.setWidget(content_container)
        self.content_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.content_dock)

    def add_reset_layout_option(self):
        """Add Reset Layout option to the menu bar."""
        menu_bar = self.menuBar()
        layout_menu = menu_bar.addMenu("Layout")

        reset_action = QAction("Reset Layout", self)
        reset_action.triggered.connect(self.reset_layout)
        layout_menu.addAction(reset_action)

    def reset_layout(self):
        """Reset the layout to the default state."""
        self.restoreState(self.default_layout)

    def show_component_frames(self, show_all=False, selected_index=None):
        """Show or hide component frames based on selection."""
        if show_all:
            # Always show vehicle frame
            self.component_frames[0].show()

            # Show only frames that have data
            for i in range(1, len(self.frames)):
                if values.geometry_data[i]:
                    self.component_frames[i].show()
        else:
            # Hide all frames except selected
            for i in self.component_frames:
                self.component_frames[i].hide()

            if selected_index is not None:
                self.component_frames[selected_index].show()

    def on_dropdown_change(self, index):
        """Change the visible frames based on the selected index of the dropdown."""
        self.show_component_frames(show_all=False, selected_index=index)

    def on_tree_item_clicked(self, item: QTreeWidgetItem, _col):
        """Show appropriate frames based on the selected item in the tree."""
        assert item is not None
        depth = 0

        item2: QTreeWidgetItem = item
        while item2.parent():
            parent = item2.parent()
            assert parent is not None
            item2 = parent
            depth += 1

        if depth == 0:
            # Clicked on Vehicle - show vehicle frame and all added components
            self.show_component_frames(show_all=True)
            return
        else:
            if depth == 1:
                top_item = item.parent()
                assert top_item is not None
                tree_index = top_item.indexOfChild(item)
                tab_index = self.find_tab_index(tree_index)
            elif depth == 2:
                component_item = item.parent()
                assert component_item is not None
                top_item = component_item.parent()
                assert top_item is not None

                tree_index = top_item.indexOfChild(component_item)
                tab_index = self.find_tab_index(tree_index)

                index = component_item.indexOfChild(item)
                frame = self.component_frames[tab_index]

                frame.load_data(values.geometry_data[tab_index][index], index)

            self.show_component_frames(show_all=False, selected_index=tab_index)

    def save_data(self, tab_index, tree_index=-1, vehicle_component=None, index=-1, data=None, new=False):
        """Save the entered data in a frame to the list.

        Args:
            tab_index: The index of the tab.
            tree_index: The index of the tab in the tree.
            index: The index of the vehicle element in the list. (Within its type, eg fuselage #0, #1, etc.)
            vehicle_component: The vehicle component to be appended to the vehicle.
            data: The data to be saved.
            new: A flag to indicate if the data is of a new element.
        """
        # print("Saving data:", data)
        if data is None:
            return

        assert tab_index >= 0
        if tab_index == 0:
            values.geometry_data[0] = data
            values.vehicle.tag = data["name"]
            for data_unit_label in VehicleFrame.data_units_labels:
                rcaide_label = data_unit_label[-1]
                user_label = data_unit_label[0]
                set_data(values.vehicle, rcaide_label, data[user_label][0])
        else:
            top_item = self.tree.topLevelItem(0)
            if tree_index == -1:
                tree_index = self.find_tree_index(tab_index)

            assert top_item is not None

            if not values.geometry_data[tab_index] or top_item.childCount() < tab_index:
                component_item = QTreeWidgetItem([self.tabs[tab_index]])
                top_item.insertChild(tree_index, component_item)
            if new:
                if index == -1:
                    values.geometry_data[tab_index].append(data)
                else:
                    frame : GeometryFrame = self.frames[tab_index]()
                    frame.load_data(data, -1)
                    vehicle_component = frame.create_rcaide_structure()
                    frame.deleteLater()

                child = QTreeWidgetItem([data["name"]])
                item = top_item.child(tree_index)
                assert item is not None
                item.addChild(child)
                index = item.indexOfChild(child)
            else:
                values.geometry_data[tab_index][index] = data
                child = top_item.child(tree_index)
                assert child is not None
                child = child.child(index)
                assert child is not None
                child.setText(0, data["name"])

        if vehicle_component:
            # Check if it is an energy network being added
            if tab_index == 5:
                values.vehicle.append_energy_network(vehicle_component)
            elif tab_index == 4:
                values.vehicle.landing_gear = vehicle_component
            else:
                values.vehicle.append_component(vehicle_component)

        return index

    def load_from_values(self):
        """Load the geometry data from the values file."""
        if values.geometry_data:
            if values.geometry_data[0]:
                self.vehicle_name_input.setText(values.geometry_data[0]["name"])
            
            for tab_index, data_list in enumerate(values.geometry_data):
                if tab_index == 0:
                    self.save_data(tab_index=tab_index, data=data_list,
                                   index=0, new=True)
                    continue

                for index, data in enumerate(data_list):
                    # tree_index = self.find_tree_index(tab_index)
                    self.save_data(tab_index=tab_index, index=index, data=data, new=True)

    # noinspection PyMethodMayBeStatic
    def find_tree_index(self, tab_index):
        # Start from tab_index - 1 to account for values.geometry_data[0] being None
        tree_index = tab_index - 1
        # Start from 1 to skip values.geometry_data[0]
        for i in range(1, tab_index):
            if not values.geometry_data[i]:
                tree_index -= 1

        tree_index = max(0, tree_index)
        return tree_index

    # noinspection PyMethodMayBeStatic
    def find_tab_index(self, tree_index):
        tab_index = 0
        count = 0

        # Start from 1 to skip values.geometry_data[0]
        for i in range(1, len(values.geometry_data)):
            if not values.geometry_data[i]:
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