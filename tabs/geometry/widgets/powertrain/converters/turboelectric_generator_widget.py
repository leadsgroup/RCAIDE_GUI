from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, QLineEdit
from RCAIDE.Library.Components.Powertrain.Converters import Turboelectric_Generator

from tabs.geometry.widgets import GeometryDataWidget
from widgets import DataEntryWidget


class TurboelectricGeneratorWidget(GeometryDataWidget):
    def __init__(self, index, on_delete, data_values=None):
        super(TurboelectricGeneratorWidget, self).__init__()

        self.index = index
        self.data_entry_widget: DataEntryWidget | None = None
        self.on_delete = on_delete

        self.main_section_layout = QVBoxLayout()

        layout = self.create_scroll_layout()

        # Segment Name layout
        self.name_layout = QHBoxLayout()
        self.section_name_edit = QLineEdit(self)
        self.name_layout.addWidget(QLabel("Converter Name: "))
        self.name_layout.addWidget(self.section_name_edit)
        layout.addLayout(self.name_layout)

        # delete_button = QPushButton("Delete Converter", self)
        # delete_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        # delete_button.clicked.connect(self.delete_button_pressed)

        # layout.addWidget(delete_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        if data_values:
            self.load_data_values(data_values, index)

    def get_data_values(self):
        title = self.section_name_edit.text()
        # data = self.data_entry_widget.get_values()
        data = {"Converter Name": title}
        # data_si = self.data_entry_widget.get_values_si()
        data_si = {}
        return data, self.create_rcaide_structure(data_si)


    def create_rcaide_structure(self, data):
        te = Turboelectric_Generator()
        te.tag = self.section_name_edit.text()
        return te

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
