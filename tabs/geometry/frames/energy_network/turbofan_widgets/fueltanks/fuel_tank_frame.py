from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, \
    QSizePolicy, QSpacerItem

from tabs.geometry.frames.energy_network.turbofan_widgets.fueltanks.fuel_tank_widget import FuelTankWidget
from tabs.geometry.frames.geometry_frame import GeometryFrame
from widgets.data_entry_widget import DataEntryWidget


class FuelTankFrame(QWidget, GeometryFrame):
    def __init__(self):
        super(FuelTankFrame, self).__init__()

        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        # List to store data values fueltank_ sections
        self.fueltank_sections_layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QVBoxLayout()
        # label = QLabel("<u><b>fueltank Frame</b></u>")

        layout = self.create_scroll_layout()

        # header_layout.addWidget(label)

        # Add fueltank_ Section Button
        add_section_button = QPushButton("Add fueltank Section", self)
        add_section_button.setMaximumWidth(200)
        add_section_button.clicked.connect(self.add_fueltank_section)

        header_layout.addWidget(add_section_button)

        layout.addLayout(header_layout)

        name_layout = QHBoxLayout()

        layout.addLayout(name_layout)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Add the layout for additional fueltank_ sections to the main layout
        layout.addLayout(self.fueltank_sections_layout)

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def get_data_values(self):
        # TODO Implement get_data_values
        pass

    def load_data(self, data, index):
        # TODO Implement load_data
        pass

    def delete_data(self):
        # TODO Implement deletion of data
        pass

    def add_fueltank_section(self):
        self.fueltank_sections_layout.addWidget(
            FuelTankWidget(self.fueltank_sections_layout.count(), self.on_delete_button_pressed))

    def on_delete_button_pressed(self, index):
        self.fueltank_sections_layout.itemAt(index).widget().deleteLater()
        self.fueltank_sections_layout.removeWidget(self.fueltank_sections_layout.itemAt(index).widget())
        self.fueltank_sections_layout.update()
        print("Deleted fueltank_ at Index:", index)

        for i in range(index, self.fueltank_sections_layout.count()):
            self.fueltank_sections_layout.itemAt(i).widget().index = i
            print("Updated Index:", i)

    def update_units(self, line_edit, unit_combobox):
        pass

    def set_save_function(self, function):
        self.save_function = function

    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Set the main layout of the widget
        self.setLayout(layout)

        return layout
