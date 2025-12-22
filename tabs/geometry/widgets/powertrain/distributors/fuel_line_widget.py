import RCAIDE
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, QLineEdit

from widgets import DataEntryWidget


class FuelLineWidget(QWidget):
    def __init__(self, index, on_delete, data_values=None):
        super(FuelLineWidget, self).__init__()

        self.index = index
        self.data_entry_widget: DataEntryWidget | None = None
        self.on_delete = on_delete

        self.main_section_layout = QVBoxLayout()

        layout = self.create_scroll_layout()

        # Segment Name layout
        self.name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        self.name_layout.addWidget(QLabel("Fuel Line Name: "))
        self.name_layout.addWidget(self.section_name_edit)
        layout.addLayout(self.name_layout) 

        delete_button = QPushButton("Delete Fuel Line", self)
        delete_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        delete_button.clicked.connect(self.delete_button_pressed)

        layout.addWidget(delete_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        if data_values:
            self.load_data_values(data_values, index)

    def delete_button_pressed(self): 
        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)

    def create_scroll_layout(self):
        # Create a widget to contain the layoutd
        scroll_content = QWidget()
        # Set the main layout inside the scroll content
        layout = QVBoxLayout(scroll_content)

        # Set the main layout of the widget
        self.setLayout(layout)

        return layout
