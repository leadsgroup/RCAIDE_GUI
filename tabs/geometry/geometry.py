from typing import Type

import RCAIDE
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QStackedLayout, QTreeWidget, QTreeWidgetItem, \
    QLabel, QLineEdit

from tabs.geometry.frames import *
from tabs import TabWidget
from utilities import set_data
import values


class GeometryWidget(TabWidget):
    def __init__(self):
        """Create a widget for entering vehicle geometry."""
        super(GeometryWidget, self).__init__()

        # Define actions based on the selected index
        self.frames: list[Type[GeometryFrame]] = [VehicleFrame, BoomFrame, CargoBayFrame, FuselageFrame, LandingGearFrame,
                                                  PowertrainFrame, WingsFrame]
        self.tabs = ["", "Booms", "Cargo Bays", "Fuselages",
                     "Landing Gear" , "Powertrain", "Wings"]

        options = ["Add Vehicle Component", "Add Boom", "Add Cargo Bay", "Add Fuselage",
                   "Add Landing Gear" , "Add Powertrain", "Add Wing"]

        values.geometry_data = []
        values.vehicle = RCAIDE.Vehicle()

        for _ in range(len(self.tabs)):
            values.geometry_data.append([])

        base_layout = QHBoxLayout()
        self.tree_frame_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        self.main_layout = QStackedLayout()

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
            frame.load_data(values.geometry_data[tab_index][index], index)

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
        if data is None:
            return

        assert tab_index >= 0
        if tab_index == 0:
            values.geometry_data[0] = data
            values.vehicle.tag = data["name"]
            for data_unit_label in VehicleFrame.data_units_labels:
                rcaide_label = data_unit_label[-1]
                user_label   = data_unit_label[0]
                set_data(values.vehicle, rcaide_label, data[user_label][0])
        else:
            top_item = self.tree.topLevelItem(0)
            assert top_item is not None
            category_name = self.tabs[tab_index]
            component_item = None
            for i in range(top_item.childCount()):
                child = top_item.child(i)
                if child.text(0) == category_name:
                    component_item = child #checking if the field like 'wings' or 'fuselages' already exists
                    break
            if component_item is None: #if the field doesnt exist, create it
                component_item = QTreeWidgetItem([category_name])
                component_item.setExpanded(True)
                insert_index = 0
                for i in range(1, tab_index):
                    if values.geometry_data[i]:
                        insert_index += 1
                top_item.insertChild(insert_index, component_item)
                    
            if new:
                if index == -1:
                    values.geometry_data[tab_index].append(data)
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
                values.geometry_data[tab_index][index] = data
                if tree_index == -1:
                    tree_index = index
                child = component_item.child(tree_index)
                if child:
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
                    self.main_layout.widget(0).update_layout()
                    continue

                for index, data in enumerate(data_list):
                    # tree_index = self.find_tree_index(tab_index)
                    self.save_data(tab_index=tab_index, index=index, data=data, new=True)
        # print(values.vehicle)


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
