# RCAIDE_GUI/tabs/geometry/widgets/geometry_data_widget.py

# Created: Dec 2025, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
from PyQt6.QtWidgets import QWidget


class GeometryDataWidget(QWidget):
    def __init__(self):
        super(GeometryDataWidget, self).__init__()

    def create_rcaide_structure(self, data):
        pass

    # Should return the data array AND the RCAIDE structure for the widget
    def get_data_values(self):
        pass

    def load_data_values(self, data):
        pass

    def delete_button_pressed(self):
        pass
