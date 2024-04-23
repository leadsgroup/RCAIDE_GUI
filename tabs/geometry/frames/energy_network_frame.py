from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from tabs.geometry.frames.geometry_frame import GeometryFrame
from utilities import show_popup, Units
from widgets.unit_picker_widget import UnitPickerWidget
from widgets.data_entry_widget import DataEntryWidget
from tabs.geometry.energy_network_widgets.turbofan_widgets.turbofan_network import TurboFanWidget
from tabs.geometry.energy_network_widgets.turbofan_widgets.fuelline_widget import FuelLineWidget

class EnergyNetworkFrame(QWidget, GeometryFrame):
   def __init__(self):
      super(EnergyNetworkFrame, self).__init__()

      self.data_fields = {}
      self.energy_network_sections_layout = QVBoxLayout()
   
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
   
      self.main_energy_network_widget = self.make_energy_network_widget()
      # Add the grid layout to the home layout
      layout.addWidget(self.main_energy_network_widget)
   
      layout.addWidget(line_bar)
      layout.addLayout(self.energy_network_sections_layout)        
   
      # Add the layout for additional energy_network sections to the main layout
   
      # Add line above the buttons
      line_above_buttons = QFrame()
      line_above_buttons.setFrameShape(QFrame.Shape.HLine)
      line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
      line_above_buttons.setStyleSheet("background-color: light grey;")
   
      layout.addWidget(line_above_buttons)
   
      # Create a QHBoxLayout to contain the buttons
      button_layout = QHBoxLayout()
   
   
      save_data_button = QPushButton("Save All Energy Network Data", self)
      save_data_button.clicked.connect(self.save_data)
      button_layout.addWidget(save_data_button)
   
   
   
      new_energy_network_structure_button = QPushButton("New Energy Network Structure", self)
      new_energy_network_structure_button.clicked.connect(self.create_new_structure)
      button_layout.addWidget(new_energy_network_structure_button)
   
   
      # Add the button layout to the main layout
      layout.addLayout(button_layout)
   
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
   
   
   
   def make_energy_network_widget(self):
         """Create a widget for the energy_network section.
   
         Returns:
             QWidget: The main energy_network widget."""
         main_energy_network_widget = QWidget()
         main_layout = QVBoxLayout()
      
         name_layout = QHBoxLayout()
         # add spacing
         spacer_left = QSpacerItem(50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
         spacer_right = QSpacerItem(200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
         name_layout.addItem(spacer_left)
         name_layout.addWidget(QLabel("Name: "))
         self.name_line_edit = QLineEdit(self)
         name_layout.addWidget(self.name_line_edit)
         name_layout.addItem(spacer_right)
         main_layout.addLayout(name_layout)

      
         # Energy Network
         energy_label = QLabel("Energy Network:")
         energy_label.setFixedWidth(100)  # Adjust width of label
         name_layout.addWidget(energy_label)
      
         self.energy_network_combo = QComboBox()
         self.energy_network_combo.addItems(["None Selected", "Turbofan"])
         self.energy_network_combo.setFixedWidth(400)  # Fix width of combo box
         name_layout.addWidget(self.energy_network_combo, alignment=Qt.AlignmentFlag.AlignLeft)
      
         # Connect signal
         self.energy_network_combo.currentIndexChanged.connect(self.display_selected_network)
      
         main_layout.addLayout(name_layout)
      
         main_energy_network_widget.setLayout(main_layout)
         return main_energy_network_widget

   

   
   def set_save_function(self, function):
         self.save_function = function
   
   def set_tab_index(self, index):
         self.tab_index = index
   
   def on_delete_button_pressed(self, index):
         self.energy_network_sections_layout.itemAt(index).widget().deleteLater()
         self.energy_network_sections_layout.removeWidget(self.energy_network_sections_layout.itemAt(index).widget())
         self.energy_network_sections_layout.update()
         print("Deleted energy_network at Index:", index)
   
         for i in range(index, self.energy_network_sections_layout.count()):
            item = self.energy_network_sections_layout.itemAt(i)
            if item is None:
               continue
   
            widget = item.widget()
            if widget is not None and isinstance(widget, TurboFanWidget):
               widget.index = i
               print("Updated Index:", i)
   
   
   def get_data_values(self):
      """Retrieve the entered data values from the widgets."""
      selected_network = self.energy_network_combo.currentText()
      data = {"energy network selected": selected_network, "name": self.name_line_edit.text()}
   
      if selected_network == "Turbofan":
         fuelline_data = []
         for index in range(self.energy_network_sections_layout.count()):
            widget = self.energy_network_sections_layout.itemAt(index).widget()
            fuelline_data.append(widget.get_data_values())      
   
         data["energy_network_sections"] = fuelline_data
   
      return data

   
   def save_data(self):
      """Call the save function and pass the entered data to it."""
      entered_data = self.get_data_values()
   
      print("Entered data in EnergyNetworkFrame:", entered_data)  # Add this line for debugging
   
      if self.save_function:
         if self.index >= 0:
            self.index = self.save_function(self.tab_index, self.index, entered_data)
            return
         else:
            self.index = self.save_function(self.tab_index, data=entered_data, new=True)
   
      show_popup("Data Saved!", self)


   
   def load_data(self, data, index):
      """Load the data into the widgets.
   
      Args:
          data: The data to be loaded into the widgets.
          index: The index of the data in the list.
      """
   
      # Load the name into the name line edit

      self.name_line_edit.setText(data["name"])
      
      # Load the selected network into the combo box
      selected_network = data.get("energy network selected", "")
      network_index = self.energy_network_combo.findText(selected_network)
      if network_index != -1:
         self.energy_network_combo.setCurrentIndex(network_index)
  
      # Clear existing sections before loading new ones
      self.clear_layout(self.energy_network_sections_layout)
  
      # Load sections based on the selected network
      if selected_network == "Turbofan":
         for section_data in data["energy_network_sections"]:
            self.energy_network_sections_layout.addWidget(FuelLineWidget(
                        self.energy_network_sections_layout.count(), self.on_delete_button_pressed, section_data))
            
            
         
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   def create_new_structure(self):
         """Create a new energy_network structure."""
   
         # Clear the main data values
         for data_field in self.data_fields.values():
            line_edit, unit_picker = data_field
            line_edit.clear()
            unit_picker.set_index(0)

         # Clear the name line edit
         while self.energy_network_sections_layout.count():
            item = self.energy_network_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
               widget.deleteLater()
   
         self.name_line_edit.clear()
         self.index = -1
   
   def delete_data(self):
         pass
      
      
      
      
      
      
   def display_selected_network(self, index):
      selected_network = self.energy_network_combo.currentText()
      # Clear the layout first
      self.clear_layout(self.energy_network_sections_layout)
   
      if selected_network == "Turbofan":
         self.main_energy_network_widget = TurboFanWidget()
         self.energy_network_sections_layout.addWidget(self.main_energy_network_widget)
      elif selected_network == "None Selected":
         # Do nothing or add blank widget
         pass
      else:
         # Handle other energy network options here
         pass
   
   def clear_layout(self, layout):
      """Clear all widgets from the layout."""
      while layout.count():
         child = layout.takeAt(0)
         if child.widget():
            child.widget().deleteLater()
