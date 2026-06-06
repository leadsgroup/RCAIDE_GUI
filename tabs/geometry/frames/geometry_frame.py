# RCAIDE_GUI/tabs/geometry/frames/geometry_frame.py
#
# Created:  Dec 2025, M. Clarke

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------
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
        return {}, RCAIDE.Library.Components.Component()
    
    def save_data(self):
        """Save the data from the frame into geometry.py, which subsequently saves it in values."""
        pass
    
    def update_layout(self):
        """Update the layout of the frame. Called when the frame is shown."""
        pass

    def wire_auto_save(self, data_entry_widget):
        """Connect data_entry_widget.data_changed to a silent save that refreshes the preview.

        Call this once per DataEntryWidget after it is constructed in a subclass __init__.
        The auto-save skips the user-facing popup and only fires for already-saved components
        (index >= 0), so it never accidentally creates new tree entries.
        """
        data_entry_widget.data_changed.connect(self._on_auto_save)

    def _on_auto_save(self):
        """Silently persist field changes and trigger a preview refresh."""
        if self.save_function is None:
            return
        # tab_index 0 is the vehicle (always present); others require an existing component.
        if self.tab_index != 0 and self.index < 0:
            return
        try:
            result = self.get_data_values()
            data = result[0] if isinstance(result, tuple) else result
        except Exception:
            return
        self.save_function(tab_index=self.tab_index, index=self.index, data=data)

