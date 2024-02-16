from tabs.geometry.frames.geometry_frame import GeometryFrame
from tabs.geometry.widgets.nacelle_section_widget import NacelleSectionWidget
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy, QLineEdit, QGridLayout, QFileDialog
from PyQt6.QtGui import QDoubleValidator

import os

from tabs.geometry.widgets.nacelle_section_widget import NacelleSectionWidget
from utilities import show_popup


class NacelleFrame(QWidget, GeometryFrame):
    def __init__(self):
        """Constructor for the NacelleFrame class."""
        super(NacelleFrame, self).__init__()
        self.data_values = {}
        self.nacelle_sections_layout = QVBoxLayout()
        self.coordinate_filename = ""
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
        header_layout.addWidget(QLabel("<b>Nacelle</b>"))

        layout.addLayout(header_layout)
        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        self.main_nacelle_widget = self.make_nacelle_widget()
        # Add the grid layout to the home layout
        layout.addWidget(self.main_nacelle_widget)

        layout.addWidget(line_bar)
        layout.addLayout(self.nacelle_sections_layout)

        # Add the layout for additional fuselage sections to the main layout

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add Nacelle Button
        add_section_button = QPushButton("Add Nacelle Section", self)
        add_section_button.clicked.connect(self.add_nacelle_section)
        button_layout.addWidget(add_section_button)

        # Append All Fuselage Section Data Button
        save_all_data_button = QPushButton("Save All Nacelle Data", self)
        # save_all_data_button.clicked.connect(self.append_all_data)
        button_layout.addWidget(save_all_data_button)

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
    
    
    def get_file_name(self):
        """Open a file dialog to select a file and store the file name.
        
        The file name is stored in the self.coordinate_filename attribute.
        """
        file_filter = "Data File (*.csv)"
        self.coordinate_filename = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.getcwd(),
            filter=file_filter
        )[0]

        print(self.coordinate_filename)


    def make_nacelle_widget(self):
        """Create a widget for the nacelle section.
        
        Returns:
            QWidget: The main nacelle widget."""
        main_nacelle_widget = QWidget()
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()

        name_layout = QHBoxLayout()
        # add spacing
        spacer_left = QSpacerItem(50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        name_layout.addItem(spacer_left)
        name_layout.addWidget(QLabel("Name: "))
        name_layout.addWidget(QLineEdit(self))
        name_layout.addItem(spacer_right)

        main_layout.addLayout(name_layout)

        # List of data labels
        data_labels = [
            "Length",
            "Inlet Diameter",
            "Diameter",
            "Origin X",
            "Origin Y",
            "Origin Z",
            "Wetted Area",
            "Flow Through",
            "Airfoil Flag",
        ]

        # Create QLineEdit frames with QDoubleValidator for numerical input
        # Create a grid layout with 3 columns
        for index, label in enumerate(data_labels):
            row, col = divmod(index, 3)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())

            # Set the width of the line edit
            line_edit.setFixedWidth(100)  # Adjust the width as needed

            grid_layout.addWidget(QLabel(label + ":"), row, col * 3)
            grid_layout.addWidget(line_edit, row, col * 3 + 1, 1, 2)

            # Store a reference to the QLineEdit in the dictionary
            self.data_values[label] = line_edit

        row, col = divmod(len(data_labels), 3)
        grid_layout.addWidget(QLabel("Coordinate File:"), row, col * 3)
        get_file_button = QPushButton("...", self)
        get_file_button.clicked.connect(self.get_file_name)
        get_file_button.setFixedWidth(100)
        grid_layout.addWidget(get_file_button, row, col * 3 + 1, 1, 2)

        main_layout.addLayout(grid_layout)

        main_nacelle_widget.setLayout(main_layout)
        return main_nacelle_widget
    

    def add_nacelle_section(self):
        self.nacelle_sections_layout.addWidget(NacelleSectionWidget(
            self.nacelle_sections_layout.count(), self.on_delete_button_pressed))
    

    def set_save_function(self, function):
        super().set_save_function(function)

        self.save_function = function
    

    def set_tab_index(self, index):
        super().set_tab_index(index)

        self.tab_index = index
    

    def on_delete_button_pressed(self, index):
        # TODO: Update indices of the nacelle widgets after the deleted index
        self.nacelle_sections_layout.itemAt(index).widget().deleteLater()
        self.nacelle_sections_layout.removeWidget(self.nacelle_sections_layout.itemAt(index).widget())
        self.nacelle_sections_layout.update()
        print("Deleted Nacelle at Index:", index)

        for i in range(index, self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None:
                continue
            
            widget = item.widget()
            if widget is not None and isinstance(widget, NacelleSectionWidget):
                widget.index = i
                print("Updated Index:", i)


    def save_data(self):
        """Append the entered data to a list or perform any other action."""
        entered_data = self.get_data_values()
        print("Saving Data:", entered_data)
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(self.tab_index, self.index, entered_data)
                return
            else:
                self.index = self.save_function(self.tab_index, data=entered_data, new=True)

        show_popup("Data Saved!", self)

    # def delete_data(self):
    #     """Delete the entered data or perform any other action."""
    #     entered_data = self.get_data_values()
    #     # Implement deletion logic here, e.g., clear the entries
    #     print("Deleting Data:", entered_data)
    #     for line_edit in self.data_values.values():
    #         line_edit.clear()
    #     show_popup("Data Erased!", self)

    # # noinspection PyTypeChecker
    def get_data_values(self):
        """Retrieve the entered data values from the dictionary."""
        temp = {}
        for key, value in self.data_values.items():
            temp[key] = value.text()
        
        temp["Coordinate File"] = self.coordinate_filename
        temp["sections"] = []
        for i in range(self.nacelle_sections_layout.count()):
            item = self.nacelle_sections_layout.itemAt(i)
            if item is None:
                continue
            
            widget = item.widget()
            if widget is not None and isinstance(widget, NacelleSectionWidget):
                temp["sections"].append(widget.get_data_values())
        
        return temp