from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame

from tabs.geometry.frames.energy_network.turbofan_widgets.fuelline_widget import FuelLineWidget
from tabs.geometry.frames.geometry_frame import GeometryFrame
from widgets.data_entry_widget import DataEntryWidget


class TurbofanWidget(QWidget):
    def __init__(self):
        super(TurbofanWidget, self).__init__()

        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        self.fuelline_sections_layout = QVBoxLayout()  # Define main_layout here

        # Header
        header_layout = QHBoxLayout()

        layout = self.create_scroll_layout()

        add_section_button = QPushButton("Add Fuel Line Section", self)
        add_section_button.setMaximumWidth(200)

        add_section_button.clicked.connect(self.add_fuelline_section)
        header_layout.addWidget(add_section_button)

        layout.addLayout(header_layout)

        name_layout = QHBoxLayout()

        layout.addLayout(name_layout)

        # Add line above buttons
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_bar)
        layout.addLayout(self.fuelline_sections_layout)

    def add_fuelline_section(self):
        self.fuelline_sections_layout.addWidget(
            FuelLineWidget(self.fuelline_sections_layout.count(), self.on_delete_button_pressed))

    def create_rcaide_structure(self, data):
        # TODO: Implement create_rcaide structure
        pass
    
    def load_data(self):
        # TODO: Implement load data
        pass

    def get_data_values(self):
        # Collect data from fuel line widgets
        data = []
        for index in range(self.fuelline_sections_layout.count()):
            widget = self.fuelline_sections_layout.itemAt(index).widget()
            data.append(widget.get_data_values())

        return data

    def on_delete_button_pressed(self, index):
        widget_item = self.fuelline_sections_layout.itemAt(index)
        if widget_item is not None:
            widget = widget_item.widget()
            self.fuelline_sections_layout.removeWidget(widget)
            self.fuelline_sections_layout.update()
            print("Deleted Fuel Line at Index:", index)

            for i in range(index, self.fuelline_sections_layout.count()):
                widget_item = self.fuelline_sections_layout.itemAt(i)
                if widget_item is not None:
                    widget = widget_item.widget()
                    widget.index = i
                    print("Updated Index:", i)

    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Set the main layout of the widget
        self.setLayout(layout)
        return layout
