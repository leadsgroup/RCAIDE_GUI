from PyQt6.QtWidgets import QVBoxLayout, QLineEdit, QWidget

import RCAIDE


class GeometryFrame(QWidget):
    def __init__(self):
        super().__init__()
        self.tab_index = -1
        self.index = -1
        self.save_function = None
        self.main_layout: QVBoxLayout | None = None
        self.name_line_edit: QLineEdit = QLineEdit()        

    def load_data(self, data, index):
        """Load the given data into the frame.
        
        Args:
            data: The data to load.
            index: The index of the data."""
        pass

    def set_save_function(self, function):
        """Set the save function to be called when the save button is pressed.

        Args:
            function: The function to be called.
        """
        self.save_function = function

    def set_tab_index(self, tab_index):
        """Set the tab index for the frame.

        Args:
            tab_index: The index of the tab."""
        self.tab_index = tab_index

    def create_new_structure(self):
        """Create a new structure for the frame: clear all fields and set the index to -1."""
        pass

    def create_rcaide_structure(self):
        """Create an RCAIDE structure from the given data and return it.
        
        Args:
            data: The data to create the structure from.
        """
        return RCAIDE.Library.Components.Component()
    
    def get_data_values(self):
        """Get the data values from the frame's widgets and return it."""
        return ({}, RCAIDE.Library.Components.Component())
    
    def save_data(self):
        """Save the data from the frame into geometry.py, which subsequently saves it in values."""
        pass
    
    def update_layout(self):
        """Update the layout of the frame. Called when the frame is shown."""
        pass
    
    
