from PyQt6.QtWidgets import QVBoxLayout, QLineEdit, QScrollArea, QWidget


class GeometryFrame:
    def __init__(self):
        self.tab_index = -1
        self.index = -1
        self.save_function = None
        self.main_layout: QVBoxLayout | None = None
        self.name_line_edit: QLineEdit | None = None

    def load_data(self, data, index):
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
        pass

    def create_rcaide_structure(self, data):
        pass
    
    def get_data_values(self):
        pass
    
    def save_data(self):
        pass
