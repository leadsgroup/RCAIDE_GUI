from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLineEdit


def create_line_bar():
    """Create a line bar to separate the widgets."""
    line_bar = QFrame()
    line_bar.setFrameShape(QFrame.Shape.HLine)
    line_bar.setFrameShadow(QFrame.Shadow.Sunken)

    return line_bar


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

    def set_tab_index(self, index):
        """Set the tab index for the frame.

        Args:
            index: The index of the tab."""
        self.tab_index = index

    def create_new_structure(self):
        pass
