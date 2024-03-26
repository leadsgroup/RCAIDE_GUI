from PyQt6.QtGui import QDoubleValidator

from PyQt6.QtWidgets import  QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QComboBox, QSizePolicy, QSpacerItem, QGridLayout
from PyQt6.QtCore import Qt

from tabs.geometry.frames.geometry_frame import GeometryFrame
from tabs.geometry.widgets.fuselage_widget import FuselageWidget
from utilities import show_popup, Units
from widgets.unit_picker_widget import UnitPickerWidget



class FuselageFrame(QWidget, GeometryFrame):
    def __init__(self):
        super(FuselageFrame, self).__init__()
        
        self.data_fields = {}
        self.fuselage_sections_layout = QVBoxLayout()
        
        self.save_function = None
        self.tab_index = -1
        self.index = -1
        self.name_line_edit: QLineEdit | None = None
        
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
        header_layout.addWidget(QLabel("<u><b>Main Fuselage Frame</b></u>"))
       
        layout.addLayout(header_layout)
        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
    
        # Add the line bar to the main layout
        layout.addWidget(line_bar)
    
        self.main_fuselage_widget = self.make_fuselage_widget()
        # Add the grid layout to the home layout
        layout.addWidget(self.main_fuselage_widget)
    
        layout.addWidget(line_bar)
        layout.addLayout(self.fuselage_sections_layout)        
        
        # Add the layout for additional fuselage sections to the main layout

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")
        
        layout.addWidget(line_above_buttons)
        
        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()
    

        add_section_button = QPushButton("Add Fuselage Section", self)
        add_section_button.clicked.connect(self.add_fuselage_section)
        button_layout.addWidget(add_section_button)


        save_data_button = QPushButton("Save All Fuselage Data", self)
        save_data_button.clicked.connect(self.save_data)
        button_layout.addWidget(save_data_button)


        delete_data_button = QPushButton("Delete Main Fuselage Frame Data", self)
        delete_data_button.clicked.connect(self.delete_data)
        button_layout.addWidget(delete_data_button)
        
        
        new_fuselage_structure_button = QPushButton("New fuselage Structure", self)
        new_fuselage_structure_button.clicked.connect(self.create_new_structure)
        button_layout.addWidget(new_fuselage_structure_button)


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



    def make_fuselage_widget(self):
        """Create a widget for the fuselage section.

        Returns:
            QWidget: The main fuselage widget."""
        main_fuselage_widget = QWidget()
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()

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
        
        
        
        # List of data labels for the main fuselage section
        data_units_labels = [
            ("Fineness Nose",Units.Length),
            ("Fineness Tail", Units.Length),
            ("Lengths Nose", Units.Length),
            ("Lengths Tail",Units.Length),
            ("Lengths Cabin",Units.Length),
            ("Lengths Total", Units.Length),
            ("Lengths Forespace", Units.Length),
            ("Lengths Aftspace", Units.Length),
            ("Width", Units.Length),
            ("Heights Maximum",Units.Length),
            ("Height at Quarter", Units.Length),
            ("Height at Three Quarters",Units.Length),
            ("Height at Wing Root Quarter Chord",Units.Length),
            ("Areas Side Projected", Units.Length),
            ("Area Wetted", Units.Length),
            ("Area Front Projected",Units.Length),
            ("Effective Diameter",Units.Length)
        ]

        for index, label in enumerate(data_units_labels):
            row, col = divmod(index, 2)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())
            # Set the width of the line edit
            line_edit.setFixedWidth(150)  # Adjust the width as needed

            unit_picker = UnitPickerWidget(label[1])
            unit_picker.setFixedWidth(80)
            grid_layout.addWidget(QLabel(label[0] + ":"), row, col * 3)
            grid_layout.addWidget(line_edit, row, col * 3 + 1, 1, 2)
            grid_layout.addWidget(unit_picker, row, col * 3 + 2, alignment=Qt.AlignmentFlag.AlignLeft)


            # Store a reference to the QLineEdit in the dictionary
            self.data_fields[label[0]] = (line_edit, unit_picker)

        main_layout.addLayout(grid_layout)
        
        main_fuselage_widget.setLayout(main_layout)
        return main_fuselage_widget
        

    def add_fuselage_section(self):
        self.fuselage_sections_layout.addWidget(FuselageWidget(
            self.fuselage_sections_layout.count(), self.on_delete_button_pressed))


    def set_save_function(self, function):
        self.save_function = function

    def set_tab_index(self, index):
        self.tab_index = index
        
    def on_delete_button_pressed(self, index):
        self.fuselage_sections_layout.itemAt(index).widget().deleteLater()
        self.fuselage_sections_layout.removeWidget(self.fuselage_sections_layout.itemAt(index).widget())
        self.fuselage_sections_layout.update()
        print("Deleted Fuselage at Index:", index)

        for i in range(index, self.fuselage_sections_layout.count()):
            item = self.fuselage_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None and isinstance(widget, FuselageWidget):
                widget.index = i
                print("Updated Index:", i)
                
    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        data = {}
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value = float(line_edit.text()) if line_edit.text() else 0.0
            data[label] = unit_picker.apply_unit(value), unit_picker.current_index

        # Get the values from the text fields
        data["name"] = self.name_line_edit.text()
        data["sections"] = []

        # Loop through the sections and get the data from each widget
        for i in range(self.fuselage_sections_layout.count()):
            item = self.fuselage_sections_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()

            # Each of the widgets has its own get_data_values method that is called to fetch their data
            if widget is not None and isinstance(widget, FuselageWidget):
                data["sections"].append(widget.get_data_values())

        return data

    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data = self.get_data_values()
        print("Saving Data:", entered_data)
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
        for label, data_field in self.data_fields.items():
            line_edit, unit_picker = data_field
            value, index = data[label]
            line_edit.setText(str(value))
            unit_picker.set_index(index)
            
        if "name" in data:
            self.name_line_edit.setText(data["name"])


        # Make sure sections don't already exist
        while self.fuselage_sections_layout.count():
            item = self.fuselage_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Add all the sections
        for section_data in data["sections"]:
            self.fuselage_sections_layout.addWidget(FuselageWidget(
                self.fuselage_sections_layout.count(), self.on_delete_button_pressed, section_data))

        self.index = index


    def create_new_structure(self):
        """Create a new fuselage structure."""

        # Clear the main data values
        for data_field in self.data_fields.values():
            line_edit, unit_picker = data_field
            line_edit.clear()
            unit_picker.set_index(0)

        # Clear the name line edit
        while self.fuselage_sections_layout.count():
            item = self.fuselage_sections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.name_line_edit.clear()
        self.index = -1
        
    def delete_data(self):
        pass