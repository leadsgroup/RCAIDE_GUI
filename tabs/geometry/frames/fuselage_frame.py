from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QComboBox, QSizePolicy, QSpacerItem, QGridLayout

from utilities import show_popup
from tabs.geometry.widgets.fuselage_widget import FuselageWidget
from widgets.color import Color


# ================================================================================================================================================

# Main Fuselage Frame

# ================================================================================================================================================

class FuselageFrame(QWidget):
    def __init__(self):
        super(FuselageFrame, self).__init__()

        self.unit_options = {
            "Fineness Nose"                         : ["NA"],
            "Fineness Tail"                         : ["NA"],
            "Lengths Nose"                          : ["cm", "m", "km"],
            "Lengths Tail"                          : ["cm", "m", "km"],
            "Lengths Cabin"                         : ["cm", "m", "km"],
            "Lengths Total"                         : ["cm", "m", "km"],
            "Lengths Forespace"                     : ["cm", "m", "km"],
            "Lengths Aftspace"                      : ["cm", "m", "km"],
            "Width"                                 : ["cm", "m", "km"],
            "Heights Maximum"                       : ["cm", "m", "km"],
            "Height at Quarter"                     : ["cm", "m", "km"],
            "Height at Three Quarters"              : ["cm", "m", "km"],
            "Height at Wing Root Quarter Chord"     : ["cm", "m", "km"],
            "Areas Side Projected"                  : ["cm\u00B2", "m\u00B2", "km\u00B2"],
            "Area Wetted"                           : ["cm\u00B2", "m\u00B2", "km\u00B2"],
            "Area Front Projected"                  : ["cm\u00B2", "m\u00B2", "km\u00B2"],
            "Effective Diameter"                    : ["cm", "m", "km"],
        }
        
        
        
        
        
        # Dictionary to store the main fuselage data
        self.main_data_values = {}

        # List to store data values fuselage sections
        self.additional_data_values = QVBoxLayout()

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget inside to resize with the scroll area

        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        label = QLabel("<u><b>Main Fuselage Frame</b></u>")
        header_layout.addWidget(label)

        # Add buttons for appending and deleting data
        #append_button = QPushButton("Append Data", self)
        delete_button = QPushButton("Delete Main Fuselage Frame Data", self)

        #append_button.clicked.connect(self.append_data)
        delete_button.clicked.connect(self.delete_data)

        #header_layout.addWidget(append_button)
        

        layout.addLayout(header_layout)
        layout.addWidget(Color("lightblue"))

        # Create a grid layout with 3 columns for main
        grid_layout = QGridLayout()

        grid_layout.addWidget(delete_button,8,3,1,2)
        
        # List of data labels for the main fuselage section
        main_data_labels = ["Fineness Nose", "Fineness Tail", "Lengths Nose", "Lengths Tail", "Lengths Cabin",
                            "Lengths Total", "Lengths Forespace", "Lengths Aftspace", "Width", "Heights Maximum",
                            "Height at Quarter", "Height at Three Quarters", "Height at Wing Root Quarter Chord",
                            "Areas Side Projected", "Area Wetted", "Area Front Projected", "Effective Diameter"]

        for index, label in enumerate(main_data_labels):
            row, col = divmod(index, 2)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())

            # Set the width of the line edit
            line_edit.setFixedWidth(100)  # Adjust the width as needed

            grid_layout.addWidget(QLabel(label + ":"), row, col * 3)
            grid_layout.addWidget(line_edit, row, col * 3 + 1, 1, 2)

            unit_combobox = QComboBox()
            unit_combobox.addItems(self.unit_options.get(label, []))
            grid_layout.addWidget(unit_combobox, row, col * 3 + 2)            
            
    
            
            # Store a reference to the QLineEdit and QComboBox in the dictionary for the main fuselage section
            self.main_data_values[label] = {
                'line_edit': line_edit,
                'unit_combobox': unit_combobox
            }

            # Connect signal to handle unit change
            unit_combobox.currentIndexChanged.connect(lambda _, le=line_edit, uc=unit_combobox: self.update_units(le, uc))


        # Add the grid layout for the main fuselage section to the main layout
        layout.addLayout(grid_layout)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Initialize additional layout for fuselage sections
        self.additional_data_values.addWidget(FuselageWidget(0,self.on_delete_button_pressed))

        # Add the layout for additional fuselage sections to the main layout
        layout.addLayout(self.additional_data_values)

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add Fuselage Section Button
        add_section_button = QPushButton("Add Fuselage Section", self)
        add_section_button.clicked.connect(self.add_fuselage_section)
        button_layout.addWidget(add_section_button)

        # Append All Fuselage Section Data Button
        append_all_data_button = QPushButton("Save All Fuselage Data", self)
        append_all_data_button.clicked.connect(self.append_all_data)
        button_layout.addWidget(append_all_data_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)

    def append_all_data(self):
        """Append the entered data to a list or perform any other action."""
        main_data = self.get_data_values()  # Get data from the main fuselage section
    
        # Collect data from additional fuselage_widget
        additional_data = []
        for index in range(self.additional_data_values.count()):
            widget = self.additional_data_values.itemAt(index).widget()
            additional_data.append(widget.get_data_values())
    
        print("Main Fuselage Data:", main_data)
        print("Additional Fuselage Data:", additional_data)
        show_popup("Data Saved!", self)


    def delete_data(self):
        """Delete the entered data or perform any other action."""
        for line_edit in self.main_data_values.values():
            line_edit.clear()
            
            

        
    def get_data_values(self):
        """Retrieve the entered data values from the dictionary for the main fuselage section."""
        main_data_values = {label: float(line_edit.text()) if line_edit.text() else 0.0
                            for label, line_edit in self.main_data_values.items()}

        return main_data_values


    def add_fuselage_section(self):
        self.additional_data_values.addWidget(FuselageWidget(self.additional_data_values.count(), self.on_delete_button_pressed))

    def on_delete_button_pressed(self, index):

        self.additional_data_values.itemAt(index).widget().deleteLater()
        self.additional_data_values.removeWidget(self.additional_data_values.itemAt(index).widget())
        self.additional_data_values.update()
        print("Deleted Fuselage at Index:", index)

        for i in range(index, self.additional_data_values.count()):
            self.additional_data_values.itemAt(i).widget().index = i
            print("Updated Index:", i)


    def update_units(self, line_edit, unit_combobox):
        pass
    