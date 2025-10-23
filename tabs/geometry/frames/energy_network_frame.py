import RCAIDE
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSpacerItem, QSizePolicy, \
    QPushButton, QLineEdit, QComboBox

from tabs.geometry.frames import GeometryFrame
from tabs.geometry.frames.energy_network.turbofan_network.widgets import TurbofanNetworkWidget, FuelLineWidget
from utilities import show_popup, clear_layout, create_line_bar

from widgets.collapsible_section import CollapsibleSection

class EnergyNetworkFrame(GeometryFrame):
    def __init__(self):
        super(EnergyNetworkFrame, self).__init__()

        self.data_fields = {}
        self.energy_network_layout = QVBoxLayout()

        self.save_function = None
        self.tab_index = -1
        self.index = -1

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        energy_network_frame_widget = QWidget()
        self.content_layout = QVBoxLayout(energy_network_frame_widget)

        self.main_energy_network_widget = self.make_energy_network_widget()
        self.content_layout.addWidget(self.main_energy_network_widget)

        self.content_layout.addWidget(create_line_bar())
        self.content_layout.addLayout(self.energy_network_layout)

        self.content_layout.addWidget(create_line_bar())

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        save_data_button = QPushButton("Save All Energy Network Data", self)
        save_data_button.clicked.connect(self.save_data)
        button_layout.addWidget(save_data_button)

        new_energy_network_structure_button = QPushButton(
            "Clear All Energy Network Data", self)
        new_energy_network_structure_button.clicked.connect(
            self.create_new_structure)
        button_layout.addWidget(new_energy_network_structure_button)

        self.content_layout.addLayout(button_layout)
        
        self.content_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        collapsible = CollapsibleSection("Energy Network Frame", energy_network_frame_widget)

        main_layout.addWidget(collapsible)

    def make_energy_network_widget(self):
        """Create a widget for the energy_network section.

        Returns:
            QWidget: The main energy_network widget."""
        main_energy_network_widget = QWidget()
        main_layout = QVBoxLayout()
        name_layout = QHBoxLayout()

        # add spacing
        spacer_left = QSpacerItem(
            50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(
            200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        name_layout.addItem(spacer_left)
        name_layout.addWidget(QLabel("Name: "))
        self.name_line_edit = QLineEdit(self)
        name_layout.addWidget(self.name_line_edit)
        name_layout.addItem(spacer_right)

        # Energy Network
        energy_label = QLabel("Energy Network:")
        energy_label.setFixedWidth(100)  # Adjust width of label
        name_layout.addWidget(energy_label)

        self.energy_network_combo = QComboBox()
        self.energy_network_combo.addItems(["None Selected", "Turbofan"])
        self.energy_network_combo.setFixedWidth(400)  # Fix width of combo box
        name_layout.addWidget(self.energy_network_combo,
                              alignment=Qt.AlignmentFlag.AlignLeft)

        # Connect signal
        self.energy_network_combo.currentIndexChanged.connect(
            self.display_selected_network)

        main_layout.addLayout(name_layout)

        main_energy_network_widget.setLayout(main_layout)
        return main_energy_network_widget

    def set_save_function(self, function):
        self.save_function = function

    def set_tab_index(self, index):
        self.tab_index = index

    def on_delete_button_pressed(self, index):
        item = self.energy_network_layout.itemAt(index)
        assert item is not None
        widget = item.widget()
        assert widget is not None
        widget.deleteLater()
        self.energy_network_layout.removeWidget(widget)
        self.energy_network_layout.update()
        print("Deleted energy_network at Index:", index)

        for i in range(index, self.energy_network_layout.count()):
            item = self.energy_network_layout.itemAt(i)
            assert item is not None

            widget = item.widget()
            assert widget is not None and isinstance(widget, FuelLineWidget)

            widget.index = i
            print("Updated Index:", i)

    def get_data_values(self):
        """Retrieve the entered data values from the widgets."""
        selected_network = self.energy_network_combo.currentText()
        data = {}
        data["energy network selected"] = selected_network

        assert self.name_line_edit is not None
        data["name"] = self.name_line_edit.text()

        if selected_network == "Turbofan":
            # Add the data values from each fuel line widget to an array
            item = self.energy_network_layout.itemAt(0)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, TurbofanNetworkWidget)
            data_values, _, __ = widget.get_data_values()

            if isinstance(data_values, bool):
                return False, False

            # add the fuel line data to the main data
            data["energy_network"] = data_values

        return data, self.create_rcaide_structure()

    def create_rcaide_structure(self):
        selected_network = self.energy_network_combo.currentText()
        
        if selected_network == "Turbofan":
            item = self.energy_network_layout.itemAt(0)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, TurbofanNetworkWidget)
            _, lines, propulsors = widget.get_data_values()

        if selected_network == "Turbofan":
            net = RCAIDE.Framework.Networks.Fuel()
            for line in lines:
                net.fuel_lines.append(line)
            
            for propulsor in propulsors:
                net.propulsors.append(propulsor)
            return net

        return None

    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data, component = self.get_data_values()
        if isinstance(entered_data, bool):
            return

        print("Entered data in EnergyNetworkFrame:",
              entered_data)  # Add this line for debugging

        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(
                    tab_index=self.tab_index, index=self.index, data=entered_data)
                return
            else:
                self.index = self.save_function(
                    tab_index=self.tab_index, vehicle_component=component, data=entered_data, new=True)

        show_popup("Data Saved!", self)

    def load_data(self, data, index):
        """Load the data into the widgets.

        Args:
            data: The data to be loaded into the widgets.
            index: The index of the data in the list.
        """

        # Load the name into the name line edit

        assert self.name_line_edit is not None
        self.name_line_edit.setText(data["name"])

        # Load the selected network into the combo box
        selected_network = data.get("energy network selected", "")
        network_index = self.energy_network_combo.findText(selected_network)
        if network_index != -1:
            self.energy_network_combo.setCurrentIndex(network_index)

        # Clear existing sections before loading new ones
        clear_layout(self.energy_network_layout)

        # Load sections based on the selected network
        if selected_network == "Turbofan":
            turbofan_widget = TurbofanNetworkWidget()
            turbofan_widget.load_data_values(data["energy_network"])
            self.energy_network_layout.addWidget(turbofan_widget)

    def create_new_structure(self):
        """Create a new energy_network structure."""

        # Clear the main data values
        for data_field in self.data_fields.values():
            line_edit, unit_picker = data_field
            line_edit.clear()
            unit_picker.set_index(0)

        # Clear the name line edit
        while self.energy_network_layout.count():
            item = self.energy_network_layout.takeAt(0)
            assert item is not None

            widget = item.widget()
            assert widget is not None
            widget.deleteLater()

        assert self.name_line_edit is not None
        self.name_line_edit.clear()
        self.index = -1

    def delete_data(self):
        pass

    def display_selected_network(self, index):
        selected_network = self.energy_network_combo.currentText()
        # Clear the layout first
        clear_layout(self.energy_network_layout)

        if selected_network == "Turbofan":
            self.main_energy_network_widget = TurbofanNetworkWidget()
            self.energy_network_layout.addWidget(
                self.main_energy_network_widget)
        elif selected_network == "None Selected":
            # Do nothing or add blank widget
            pass
        else:
            # Handle other energy network options here
            pass