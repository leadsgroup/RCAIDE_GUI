from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, \
    QSizePolicy, QSpacerItem

from tabs.geometry.widgets.powertrain.distributors import DistributorWidget
from widgets import DataEntryWidget

class DistributorFrame(QWidget):
    def __init__(self):
        super(DistributorFrame, self).__init__()

        self.save_function = None
        self.data_entry_widget: DataEntryWidget | None = None

        # List to store data values source_ sections
        self.distributor_sections_layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QVBoxLayout()
        # label = QLabel("<u><b>source Frame</b></u>")

        layout = self.create_scroll_layout()

        # header_layout.addWidget(label)

        # Add source_ Section Button
        add_section_button = QPushButton("Add Energy Source", self)
        add_section_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        add_section_button.setMaximumWidth(200)
        add_section_button.clicked.connect(self.add_source_section)

        header_layout.addWidget(add_section_button)

        layout.addLayout(header_layout)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Add the layout for additional source_ sections to the main layout
        layout.addLayout(self.distributor_sections_layout)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def get_data_values(self):
        data = []
        sources = []
        for index in range(self.distributor_sections_layout.count()):
            item = self.distributor_sections_layout.itemAt(index)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, DistributorWidget)

            source_data, fuel_tank = widget.get_data_values()
            data.append(source_data)
            sources.append(fuel_tank)

        return data, sources

    def load_data(self, data):
        while self.distributor_sections_layout.count():
            widget_item = self.distributor_sections_layout.itemAt(0)
            assert widget_item is not None
            widget = widget_item.widget()
            assert widget is not None

            self.distributor_sections_layout.removeWidget(widget)
            widget.deleteLater()

        for section_data in data:
            self.distributor_sections_layout.addWidget(DistributorWidget(
                self.distributor_sections_layout.count(), self.on_delete_button_pressed, section_data))

    def delete_data(self):
        # TODO Implement proper deletion of data
        pass

    def add_source_section(self):
        self.distributor_sections_layout.addWidget(
            DistributorWidget(self.distributor_sections_layout.count(), self.on_delete_button_pressed))

    def on_delete_button_pressed(self, index):
        distributor = self.distributor_sections_layout.itemAt(index)
        if distributor is None:
            return

        widget = distributor.widget()
        if widget is None:
            return

        widget.deleteLater()
        self.distributor_sections_layout.removeWidget(widget)
        self.distributor_sections_layout.update() 

        for i in range(index, self.distributor_sections_layout.count()):
            distributor = self.distributor_sections_layout.itemAt(i)
            if distributor is None:
                continue

            widget = distributor.widget()
            if widget is None or not isinstance(widget, DistributorWidget):
                continue

            widget.index = i 

    def set_save_function(self, function):
        self.save_function = function

    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        
        # Set the main layout inside the scroll content
        layout = QVBoxLayout(scroll_content)

        # Set the main layout of the widget
        self.setLayout(layout)

        return layout
