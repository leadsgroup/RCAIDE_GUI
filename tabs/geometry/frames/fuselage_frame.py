from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, \
    QSizePolicy, QSpacerItem, QGridLayout

from utilities import show_popup
from widgets.color import Color


# ================================================================================================================================================

# Main Fuselage Frame

# ================================================================================================================================================

class FuselageFrame(QWidget):
    def __init__(self):
        super(FuselageFrame, self).__init__()

        # Dictionary to store the entered values for the main
        self.main_data_values = {}

        # List to store data values for additional fuselage sections
        self.additional_data_values = []

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget inside to resize with the scroll area

        # Create a widget to contain the layout
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)  # Set the main layout inside the scroll content

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        label = QLabel("<u><b>Fuselage Frame</b></u>")
        header_layout.addWidget(label)

        # Add buttons for appending and deleting data
        append_button = QPushButton("Append Data", self)
        delete_button = QPushButton("Delete Data", self)

        append_button.clicked.connect(self.append_data)
        delete_button.clicked.connect(self.delete_data)

        header_layout.addWidget(append_button)
        header_layout.addWidget(delete_button)

        layout.addLayout(header_layout)
        layout.addWidget(Color("lightblue"))

        # Create a grid layout with 3 columns for main
        grid_layout = QGridLayout()

        # List of data labels for the main fuselage section
        main_data_labels = ["Fineness Nose", "Fineness Tail", "Lengths Nose", "Lengths Tail", "Lengths Cabin",
                            "Lengths Total", "Lengths Forespace", "Lengths Aftspace", "Width", "Heights Maximum",
                            "Height at Quarter", "Height at Three Quarters", "Height at Wing Root Quarter Chord",
                            "Areas Side Projected", "Area Wetted", "Area Front Projected", "Effective Diameter"]

        for index, label in enumerate(main_data_labels):
            row, col = divmod(index, 3)
            line_edit = QLineEdit(self)
            line_edit.setValidator(QDoubleValidator())

            # Set the width of the line edit
            line_edit.setFixedWidth(100)  # Adjust the width as needed

            grid_layout.addWidget(QLabel(label + ":"), row, col * 3)
            grid_layout.addWidget(line_edit, row, col * 3 + 1, 1, 2)

            # Store a reference to the QLineEdit in the dictionary for the main fuselage section
            self.main_data_values[label] = line_edit

        # Add the grid layout for the main fuselage section to the main layout
        layout.addLayout(grid_layout)

        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        line_bar.setStyleSheet("background-color: white;")

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        # Initialize additional layout for fuselage sections
        self.additional_layout = QVBoxLayout()

        # Add the layout for additional fuselage sections to the main layout
        layout.addLayout(self.additional_layout)

        # Add line above the buttons
        line_above_buttons = QFrame()
        line_above_buttons.setFrameShape(QFrame.Shape.HLine)
        line_above_buttons.setFrameShadow(QFrame.Shadow.Sunken)
        line_above_buttons.setStyleSheet("background-color: white;")

        layout.addWidget(line_above_buttons)

        # Create a QHBoxLayout to contain the buttons
        button_layout = QHBoxLayout()

        # Add Fuselage Section Button
        add_section_button = QPushButton("Add Fuselage Section", self)
        add_section_button.clicked.connect(self.add_fuselage_section)
        button_layout.addWidget(add_section_button)

        # Append All Fuselage Section Data Button
        append_all_data_button = QPushButton("Append All Fuselage Section Data", self)
        append_all_data_button.clicked.connect(self.append_all_data)
        button_layout.addWidget(append_all_data_button)

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

    def append_data(self):
        """Append the entered data to a list or perform any other action."""
        entered_data = self.get_data_values()
        # Implement appending logic here, e.g., append to a list
        print("Appending Data:", entered_data)
        show_popup("Data Saved!", self)

    def delete_data(self):
        """Delete the entered data or perform any other action."""
        entered_data = self.get_data_values()
        # Implement deletion logic here, e.g., clear the entries
        print("Deleting Data:", entered_data)
        for line_edit in self.main_data_values.values():
            line_edit.clear()

        # Clear data for additional fuselage sections
        for data_values in self.additional_data_values:
            for line_edit in data_values.values():
                line_edit.clear()

        # Clear additional fuselage sections
        for i in reversed(range(self.additional_layout.count())):
            item = self.additional_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)

        show_popup("Data Erased!", self)

    def get_data_values(self):
        """Retrieve the entered data values from the dictionary for the main fuselage section."""
        main_data_values = {label: float(line_edit.text()) if line_edit.text() else 0.0
                            for label, line_edit in self.main_data_values.items()}

        # Retrieve the entered data values from the list for additional fuselage sections
        additional_data_values = [{label + f"_{i}": float(line_edit.text()) if line_edit.text() else 0.0
                                   for label, line_edit in data_values.items()}
                                  for i, data_values in enumerate(self.additional_data_values, start=1)]

        return {"main_data": main_data_values, "additional_data": additional_data_values}

    # ================================================================================================================================================

    # Fuselage Section

    # ================================================================================================================================================

    def add_fuselage_section(self):
        """Add a new fuselage section with input boxes for Percent X Location, Percent Z Location, Height, and Width."""
        additional_section_layout = QGridLayout()

        # Add segment number label
        segment_label = QLabel()
        segment_label.setText(f"<b><u>Segment {len(self.additional_data_values)}</b></u>")
        additional_section_layout.addWidget(segment_label)

        percent_x_location = QLineEdit(self)
        percent_x_location.setValidator(QDoubleValidator())
        percent_x_location.setFixedWidth(100)

        percent_z_location = QLineEdit(self)
        percent_z_location.setValidator(QDoubleValidator())
        percent_z_location.setFixedWidth(100)

        height = QLineEdit(self)
        height.setValidator(QDoubleValidator())
        height.setFixedWidth(100)

        width = QLineEdit(self)
        width.setValidator(QDoubleValidator())
        width.setFixedWidth(100)

        additional_section_layout.addWidget(QLabel("Percent X Location:"), 1, 0)
        additional_section_layout.addWidget(percent_x_location, 1, 4, 1, 2)

        additional_section_layout.addWidget(QLabel("Percent Z Location:"), 2, 0)
        additional_section_layout.addWidget(percent_z_location, 2, 4, 1, 2)

        additional_section_layout.addWidget(QLabel("Height:"), 1, 2 * 3)
        additional_section_layout.addWidget(height, 1, 9, 1, 4)

        additional_section_layout.addWidget(QLabel("Width:"), 2, 2 * 3)
        additional_section_layout.addWidget(width, 2, 9, 1, 4)

        delete_section_button = QPushButton("Delete Fuselage Section", self)
        append_data_button = QPushButton("Append Fuselage Section Data", self)

        delete_section_button.clicked.connect(self.delete_and_display_data)

        # Connect the "Append Fuselage Section Data" button to a lambda function
        # that captures the index of the button and calls append_section_data with that index
        append_data_button.clicked.connect(
            lambda _, index=len(self.additional_data_values): self.append_section_data(index))

        # Add buttons to the layout
        additional_section_layout.addWidget(delete_section_button, 1, 4 * 3 + 1, 1, 2)
        additional_section_layout.addWidget(append_data_button, 2, 4 * 3 + 1, 1, 2)

        self.additional_layout.addLayout(additional_section_layout)
        self.additional_data_values.append({"Percent X Location": percent_x_location,
                                            "Percent Z Location": percent_z_location,
                                            "Height": height,
                                            "Width": width})

        print("Number of sections after addition:", len(self.additional_data_values))  # Debugging statement

    def append_section_data(self, section_index):
        """Append the entered data for the specified fuselage section."""
        entered_data = self.get_section_data_values(section_index)
        print("Appending Section Data for section", section_index, ":", entered_data)

        show_popup("Section Data Saved!", self)

    def get_section_data_values(self, section_index):
        """Retrieve the entered data values for the specified fuselage section."""
        data_values = self.additional_data_values[section_index]
        return {label: float(line_edit.text()) if line_edit.text() else 0.0
                for label, line_edit in data_values.items()}

    def delete_section(self):
        """Deletes the fuselage section."""
        try:
            print("Number of sections before deletion:", len(self.additional_data_values))  # Debugging statement
            if self.additional_data_values:
                # Remove widgets from layout
                layout_item = self.additional_layout.itemAt(self.additional_layout.count() - 1)
                if layout_item is not None:
                    for i in reversed(range(layout_item.layout().count())):
                        widget = layout_item.layout().itemAt(i).widget()
                        layout_item.layout().removeWidget(widget)
                        widget.deleteLater()

                    # Remove the layout item if the layout is empty
                    if layout_item.layout().count() == 0:
                        self.additional_layout.removeItem(layout_item)

                # Remove the data from the list
                self.additional_data_values.pop()
            else:
                print("No sections to delete.")

            # Debugging statement to check the number of sections after deletion
            print("Number of sections after deletion:", len(self.additional_data_values))
        except Exception as e:
            print(f"An error occurred while deleting section: {e}")

    def display_data(self):
        """Displays the data after a section is deleted."""
        # \\print("Updated Section Data after deletion:", self.get_section_data_values())
        pass

    def delete_and_display_data(self):
        """Combining display_data and delete_section function so button can call both."""
        self.delete_section()
        self.display_data()

    def append_all_data(self):
        """Append the entered data for the additional fuselage section."""
        all_entered_data = self.get_all_data_values()
        print("Appending All Data:", all_entered_data)

        show_popup("Section Data Saved!", self)

    def get_all_data_values(self):
        """Retrieve the entered data values for additional fuselage sections."""
        return [{label + f"_{i}": float(line_edit.text()) if line_edit.text() else 0.0
                 for label, line_edit in data_values.items()}
                for i, data_values in enumerate(self.additional_data_values, start=1)]
