from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QLineEdit, QPushButton

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Create layouts
        base_layout = QVBoxLayout()

        # Create the initial horizontal layout for the title, input box, and "Create" button
        self.horizontal_layouts = []  # Maintain a list to keep track of created horizontal layouts
        self.add_horizontal_layout()

        # Add the initial horizontal layout to the main vertical layout
        base_layout.addLayout(self.horizontal_layouts[0])

        # Set spacings
        base_layout.setSpacing(3)

        # Set up the base widget
        base_widget = QWidget()
        base_widget.setLayout(base_layout)

        self.setLayout(base_layout)

    def add_horizontal_layout(self):
        # Create a new horizontal layout for the title, input box, and "Create" button
        new_horizontal_layout = QHBoxLayout()

        # Add a QLabel with the title "Energy Network Frame" to the left side of the horizontal layout
        title_label = QLabel("Mission Name:")
        new_horizontal_layout.addWidget(title_label)

        # Add a QLineEdit (input box) to the right side of the horizontal layout
        mission_name_input = QLineEdit(self)
        new_horizontal_layout.addWidget(mission_name_input)

        # Add a "Create" button to the horizontal layout
        create_button = QPushButton("Append Segment", self)
        create_button.clicked.connect(self.create_action)  # Connect the button click to a function (create_action)
        new_horizontal_layout.addWidget(create_button)

        # Add the new horizontal layout to the list
        self.horizontal_layouts.append(new_horizontal_layout)

    def add_new_horizontal_layout(self):
        # Create a new horizontal layout for the label, dropdown menu, and button
        new_horizontal_layout = QHBoxLayout()

        # Add a QLabel
        label = QLabel("Segment Type:")
        new_horizontal_layout.addWidget(label)

        # Add a QComboBox (dropdown menu)
        combo_box = QComboBox(self)
        options = ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"]
        combo_box.addItems(options)
        new_horizontal_layout.addWidget(combo_box)

        # Add a QLabel
        label = QLabel("Segment Name:")
        new_horizontal_layout.addWidget(label)

        # Add a QLineEdit
        line_edit = QLineEdit(self)
        new_horizontal_layout.addWidget(line_edit)

        # Add a "Delete" button to the horizontal layout
        delete_button = QPushButton("Delete", self)
        delete_button.clicked.connect(lambda: self.delete_horizontal_layout(new_horizontal_layout))
        new_horizontal_layout.addWidget(delete_button)

        # Get the main layout
        main_layout = self.layout()

        # Insert the new horizontal layout below the first one
        main_layout.insertLayout(1, new_horizontal_layout)  # Assuming the first layout is at index 1

        # Add the new horizontal layout to the list
        self.horizontal_layouts.append(new_horizontal_layout)

    def delete_horizontal_layout(self, layout):
        """Delete the last added horizontal layout."""
        try:
            print("Number of layouts before deletion:", len(self.horizontal_layouts))  # Debugging statement
            if self.horizontal_layouts:
                # Get the main layout
                main_layout = self.layout()

                # Remove the widgets from the layout
                for i in reversed(range(layout.count())):
                    widget = layout.itemAt(i).widget()
                    layout.removeWidget(widget)
                    widget.deleteLater()

                # Remove the layout item if the layout is empty
                if layout.count() == 0:
                    main_layout.removeItem(layout)

                # Remove the layout from the list
                self.horizontal_layouts.remove(layout)

                print("Number of layouts after deletion:", len(self.horizontal_layouts))  # Debugging statement
            else:
                print("No layouts to delete.")
        except Exception as e:
            print(f"An error occurred while deleting layout: {e}")

    def create_action(self):
        # This function will be called when the "Create" button is clicked
        print("Create button clicked!")

        # Add a new horizontal layout for the title, input box, and "Create" button
        self.add_new_horizontal_layout()

        # Add the new horizontal layout to the main layout
        self.layout().addLayout(self.horizontal_layouts[-1])

# Function to get the widget
def get_widget() -> QWidget:
    return MyWidget()
