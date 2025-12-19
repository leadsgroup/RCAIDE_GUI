import RCAIDE
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSpacerItem, QSizePolicy, \
    QPushButton, QLineEdit, QComboBox

from tabs.geometry.frames import GeometryFrame
from tabs.geometry.widgets.powertrain.powertrain_widget   import PowertrainWidget  
from utilities import show_popup, clear_layout


class PowertrainFrame(GeometryFrame):
    def __init__(self):
        super(PowertrainFrame, self).__init__()

        self.data_fields = {}
        self.powertrain_layout = QVBoxLayout()

        self.save_function = None
        self.tab_index = -1
        self.index = -1

        # Create a scroll area
        scroll_area = QScrollArea()
        # Allow the widget inside to resize with the scroll area
        scroll_area.setWidgetResizable(True)

        # Create a widget to contain the layout
        scroll_content = QWidget()
        # Set the main layout inside the scroll content
        layout = QVBoxLayout(scroll_content)

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Energy Network Frame</b>"))

        layout.addLayout(header_layout)
        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        self.main_powertrain_widget = self.make_powertrain_widget()
        # Add the grid layout to the home layout
        layout.addWidget(self.main_powertrain_widget)

        layout.addWidget(line_bar)
        layout.addLayout(self.powertrain_layout) 

        self.add_buttons_layout()        

        # Adds scroll function
        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self):
        # define buttons 
        propulsor_button = QPushButton("Add Propulsor", self)
        propulsor_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        distributor_button = QPushButton("Add Distributor", self)
        distributor_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        converter_button = QPushButton("Add Converter", self)
        converter_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        source_button = QPushButton("Add Energy Source", self)
        source_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;") 
        save_button = QPushButton("Save Energy Network Data", self)
        save_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        delete_button = QPushButton("Clear Energy Network", self)
        delete_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
   
        # define action of buttons
        #propulsor_button.clicked.connect(self.add_propulsor) 
        #distributor_button.clicked.connect(self.add_distributor) 
        #converter_button.clicked.connect(self.add_converter) 
        #source_button.clicked.connect(self.add_energy_source) 
        save_button.clicked.connect(self.save_data)
        delete_button.clicked.connect( self.create_new_structure)   

        # Create a QHBoxLayout to contain the buttons
        buttons_layout = QHBoxLayout() 
        buttons_layout.addWidget(distributor_button) 
        buttons_layout.addWidget(propulsor_button) 
        buttons_layout.addWidget(converter_button)
        buttons_layout.addWidget(source_button)
        buttons_layout.addWidget(save_button) 
        buttons_layout.addWidget(delete_button)  

        assert self.powertrain_layout is not None
        self.powertrain_layout.addLayout(buttons_layout)
        
        
    def make_powertrain_widget(self):
        """Create a widget for the powertrain section.

        Returns:
            QWidget: The main powertrain widget."""
        main_powertrain_widget = QWidget()
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
        self.powertrain_combo = QComboBox()
        self.powertrain_combo.addItems(["None Selected", "Fuel", "Electric", "Hydrogen", "Hybrid"])
        self.powertrain_combo.setFixedWidth(400)  # Fix width of combo box
        name_layout.addWidget(self.powertrain_combo,  alignment=Qt.AlignmentFlag.AlignLeft)

        # Connect signal
        self.powertrain_combo.currentIndexChanged.connect(
            self.display_selected_network)

        main_layout.addLayout(name_layout)

        main_powertrain_widget.setLayout(main_layout)
        return main_powertrain_widget
 
    #def add_energy_source(self):
        #self.energy_sources_layout.addWidget(EnergySourceWidget(
            #self.energy_sources_layout.count(), self.delete_energy_source))

    #def delete_energy_source(self, index):
        #item = self.energy_sources_layout.itemAt(index)
        #assert item is not None
        #widget = item.widget()
        #assert widget is not None and isinstance(widget, EnergySourceWidget)

        #widget.deleteLater()
        #self.energy_sources_layout.removeWidget(widget)
        #self.energy_sources_layout.update()

        #for i in range(index, self.energy_sources_layout.count()):
            #item = self.energy_sources_layout.itemAt(i)
            #if item is None:
                #continue

            #widget = item.widget()
            #if widget is not None and isinstance(widget, EnergySourceWidget):
                #widget.index = i        
        
    def set_save_function(self, function):
        self.save_function = function

    def set_tab_index(self, index):
        self.tab_index = index

    #def on_delete_button_pressed(self, index):
        #item = self.powertrain_layout.itemAt(index)
        #assert item is not None
        #widget = item.widget()
        #assert widget is not None
        #widget.deleteLater()
        #self.powertrain_layout.removeWidget(widget)
        #self.powertrain_layout.update()
        #print("Deleted powertrain at Index:", index)

        #for i in range(index, self.powertrain_layout.count()):
            #item = self.powertrain_layout.itemAt(i)
            #assert item is not None

            #widget = item.widget()
            #assert widget is not None and isinstance(widget, DistributorWidget)

            #widget.index = i
            #print("Updated Index:", i)

    def get_data_values(self):
        """Retrieve the entered data values from the widgets."""
        selected_network = self.powertrain_combo.currentText()
        data = {}
        data["energy network selected"] = selected_network

        assert self.name_line_edit is not None
        data["name"] = self.name_line_edit.text()

        if selected_network == "Turbofan":
            # Add the data values from each fuel line widget to an array
            item = self.powertrain_layout.itemAt(0)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, PowertrainWidget)
            data_values, _, __ = widget.get_data_values()

            if isinstance(data_values, bool):
                return False, False

            # add the fuel line data to the main data
            data["powertrain"] = data_values

        return data, self.create_rcaide_structure()

    def create_rcaide_structure(self):
        selected_network = self.powertrain_combo.currentText()
        
        if selected_network == "Fuel":
            item = self.powertrain_layout.itemAt(0)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, PowertrainWidget)
            _, lines, propulsors = widget.get_data_values()

        if selected_network == "Fuel":
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

        print("Entered data in PowertrainFrame:",
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
        network_index = self.powertrain_combo.findText(selected_network)
        if network_index != -1:
            self.powertrain_combo.setCurrentIndex(network_index)

        # Clear existing sections before loading new ones
        clear_layout(self.powertrain_layout)

        # Load sections based on the selected network
        if selected_network == "Turbofan":
            turbofan_widget = PowertrainWidget()
            turbofan_widget.load_data_values(data["powertrain"])
            self.powertrain_layout.addWidget(turbofan_widget)

    def create_new_structure(self):
        """Create a new powertrain structure."""

        # Clear the main data values
        for data_field in self.data_fields.values():
            line_edit, unit_picker = data_field
            line_edit.clear()
            unit_picker.set_index(0)

        # Clear the name line edit
        while self.powertrain_layout.count():
            item = self.powertrain_layout.takeAt(0)
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
        selected_network = self.powertrain_combo.currentText()
        # Clear the layout first
        clear_layout(self.powertrain_layout)

        if selected_network == "Fuel":
            self.main_powertrain_widget = PowertrainWidget()
            self.powertrain_layout.addWidget(self.main_powertrain_widget)
        elif selected_network == "None Selected":
            # Do nothing or add blank widget
            pass
        else:
            # Handle other energy network options here
            pass