from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

from tabs.geometry.widgets.nacelle_widget import NacelleWidget
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QScrollArea, \
    QFrame, QSpacerItem, QSizePolicy

from tabs.geometry.widgets.nacelle_widget import NacelleWidget


class NacelleFrame(QWidget):
    def __init__(self):
        super(NacelleFrame, self).__init__()
        self.data_values = {}
        self.data_entry_layout = QVBoxLayout()

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget inside to resize with the scroll area

        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Nacelles</b>"))

        layout.addLayout(header_layout)
        # layout.addWidget(Color("lightblue"))

        # Create a grid layout with 3 columns

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Add the grid layout to the home layout
        self.data_entry_layout.addWidget(NacelleWidget(0, self.on_delete_button_pressed))
        layout.addLayout(self.data_entry_layout)

        # Add the layout for additional fuselage sections to the main layout

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: light grey;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add Nacelle Button
        add_section_button = QPushButton("Add Nacelle", self)
        add_section_button.clicked.connect(self.add_nacelle)
        button_layout.addWidget(add_section_button)

        # Append All Fuselage Section Data Button
        save_all_data_button = QPushButton("Save All Nacelle Data", self)
        # save_all_data_button.clicked.connect(self.append_all_data)
        button_layout.addWidget(save_all_data_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Adds scroll function
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)

    # def append_data(self):
    #     """Append the entered data to a list or perform any other action."""
    #     entered_data = self.get_data_values()
    #     # Implement appending logic here, e.g., append to a list
    #     print("Appending Data:", entered_data)
    #     show_popup("Data Saved!", self)

    # def delete_data(self):
    #     """Delete the entered data or perform any other action."""
    #     entered_data = self.get_data_values()
    #     # Implement deletion logic here, e.g., clear the entries
    #     print("Deleting Data:", entered_data)
    #     for line_edit in self.data_values.values():
    #         line_edit.clear()
    #     show_popup("Data Erased!", self)

    # # noinspection PyTypeChecker
    # def get_data_values(self):
    #     """Retrieve the entered data values from the dictionary."""
    #     temp = {label: float(line_edit.text()) if line_edit.text() else 0.0
    #             for label, line_edit in self.data_values.items()}
    #     temp["Coordinate Filename"] = self.coordinate_filename
    #     return temp

    def add_nacelle(self):
        self.data_entry_layout.addWidget(NacelleWidget(self.data_entry_layout.count(), self.on_delete_button_pressed))

    def on_delete_button_pressed(self, index):
        # TODO: Update indices of the nacelle widgets after the deleted index
        self.data_entry_layout.itemAt(index).widget().deleteLater()
        self.data_entry_layout.removeWidget(self.data_entry_layout.itemAt(index).widget())
        self.data_entry_layout.update()
        print("Deleted Nacelle at Index:", index)

        for i in range(index, self.data_entry_layout.count()):
            self.data_entry_layout.itemAt(i).widget().index = i
            print("Updated Index:", i)
