from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, \
    QSizePolicy, QSpacerItem, QLineEdit

from tabs.geometry.frames.geometry_frame import GeometryFrame

from utilities import show_popup, Units
from widgets.data_entry_widget import DataEntryWidget
from tabs.geometry.energy_network_widgets.turbofan_widgets.propulsors.propulsors_widget import PropulsorWidget

class PropulsorFrame(QWidget, GeometryFrame):
    def __init__(self):
        super(PropulsorFrame, self).__init__()

        self.index = -1
        self.tab_index = -1
        self.save_function = None
        self.data_entry_widget : DataEntryWidget | None = None


        # List to store data values propulsor_ sections
        self.propulsor_sections_layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QVBoxLayout()
        #label = QLabel("<u><b>Propulsor Frame</b></u>")

        layout = self.create_scroll_layout()

        #header_layout.addWidget(label)
        
        
        # Add propulsor_ Section Button
        add_section_button = QPushButton("Add Propulsor Segment", self)
        add_section_button.setMaximumWidth(200) 
        add_section_button.clicked.connect(self.add_propulsor_section)
        header_layout.addWidget(add_section_button)
        
    
        
        
        layout.addLayout(header_layout)

        name_layout = QHBoxLayout()

        layout.addLayout(name_layout)



        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Add the layout for additional propulsor_ sections to the main layout
        layout.addLayout(self.propulsor_sections_layout)

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()



        ## Append All propulsor_ Section Data Button
        #append_all_data_button = QPushButton("Save Propulsor Data", self)
        #append_all_data_button.clicked.connect(self.save_data)
        #button_layout.addWidget(append_all_data_button)


        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def get_data_values(self):
        """Retrieve the entered data values from the dictionary for the propulsor sections."""

        # Collect data from additional fuselage_widget
        additional_data = []
        for index in range(self.propulsor_sections_layout.count()):
            widget = self.propulsor_sections_layout.itemAt(index).widget()
            additional_data.append(widget.get_data_values())

        #data["sections"] = additional_data
        return additional_data

    def save_data(self):
        """Append the entered data to a list or perform any other action."""
        entered_data = self.get_data_values()

        print("Propulsor Data:", entered_data)

        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(self.tab_index, self.index, entered_data)
                return
            else:
                self.index = self.save_function(self.tab_index, data=entered_data, new=True)

            show_popup("Data Saved!", self)

    def load_data(self, data, index):
        self.data_entry_widget.load_data(data)
        self.name_line_edit.setText(data["name"])

        # Make sure sections don't already exist
        while self.propulsor_sections_layout.count():
            item = self.propulsor_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for section_data in data["sections"]:
            self.propulsor_sections_layout.addWidget(PropulsorWidget(
                self.propulsor_sections_layout.count(), self.on_delete_button_pressed, section_data))

    def delete_data(self):
        """Delete the entered data or perform any other action."""
        self.data_entry_widget.clear_values()

    def add_propulsor_section(self):
        self.propulsor_sections_layout.addWidget(
            PropulsorWidget(self.propulsor_sections_layout.count(), self.on_delete_button_pressed))

    def on_delete_button_pressed(self, index):
        self.propulsor_sections_layout.itemAt(index).widget().deleteLater()
        self.propulsor_sections_layout.removeWidget(self.propulsor_sections_layout.itemAt(index).widget())
        self.propulsor_sections_layout.update()
        print("Deleted propulsor_ at Index:", index)

        for i in range(index, self.propulsor_sections_layout.count()):
            self.propulsor_sections_layout.itemAt(i).widget().index = i
            print("Updated Index:", i)

    def update_units(self, line_edit, unit_combobox):
        pass

    def set_save_function(self, function):
        self.save_function = function

    def set_tab_index(self, index):
        self.tab_index = index



    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content
    
        # Set the main layout of the widget
        self.setLayout(layout)
    
        return layout