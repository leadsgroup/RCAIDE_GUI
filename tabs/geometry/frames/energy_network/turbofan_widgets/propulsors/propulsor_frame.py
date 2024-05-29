from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, \
    QSizePolicy, QSpacerItem

from tabs.geometry.frames.energy_network.turbofan_widgets.propulsors.propulsor_widget import PropulsorWidget
from widgets.data_entry_widget import DataEntryWidget


class PropulsorFrame(QWidget):
    def __init__(self):
        super(PropulsorFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        # List to store data values propulsor_ sections
        self.propulsor_sections_layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QVBoxLayout()
        # label = QLabel("<u><b>Propulsor Frame</b></u>")

        layout = self.create_scroll_layout()

        # header_layout.addWidget(label)

        # Add propulsor_ Section Button
        add_section_button = QPushButton("Add Propulsor Segment", self)
        add_section_button.setMaximumWidth(200)
        add_section_button.clicked.connect(self.add_propulsor_section)
        header_layout.addWidget(add_section_button)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: light grey;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Add the layout for additional propulsor_ sections to the main layout
        layout.addLayout(self.propulsor_sections_layout)

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
        """Retrieve the entered data values from the dictionary for the propulsor sections."""

        # Collect data from additional fuselage_widget
        data = []
        for index in range(self.propulsor_sections_layout.count()):
            item = self.propulsor_sections_layout.itemAt(index)
            if item is None:
                continue
            
            widget = item.widget()
            if widget is None or not isinstance(widget, PropulsorWidget):
                continue
            
            data.append(widget.get_data_values())

        return data

    def load_data(self, data):
        # Make sure sections don't already exist
        while self.propulsor_sections_layout.count():
            item = self.propulsor_sections_layout.takeAt(0)
            if item is None:
                continue
            
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for section_data in data:
            self.propulsor_sections_layout.addWidget(PropulsorWidget(
                self.propulsor_sections_layout.count(), self.on_delete_button_pressed, section_data))

    def delete_data(self):
        """Delete the entered data or perform any other action."""
        # TODO: Implement proper deletion of data

    def add_propulsor_section(self):
        self.propulsor_sections_layout.addWidget(
            PropulsorWidget(self.propulsor_sections_layout.count(), self.on_delete_button_pressed))

    def on_delete_button_pressed(self, index):
        propulsor = self.propulsor_sections_layout.itemAt(index)
        if propulsor is None:
            return
        
        widget = propulsor.widget()
        if widget is None:
            return
        
        widget.deleteLater()
        self.propulsor_sections_layout.removeWidget(widget)
        self.propulsor_sections_layout.update()
        print("Deleted propulsor_ at Index:", index)

        for i in range(index, self.propulsor_sections_layout.count()):
            propulsor = self.propulsor_sections_layout.itemAt(i)
            if propulsor is None:
                continue
            
            widget = propulsor.widget()
            if widget is None or not isinstance(widget, PropulsorWidget):
                continue
            
            widget.index = i
            print("Updated Index:", i)

    def update_units(self, line_edit, unit_combobox):
        pass

    def create_scroll_layout(self):
        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Set the main layout of the widget
        self.setLayout(layout)

        return layout
