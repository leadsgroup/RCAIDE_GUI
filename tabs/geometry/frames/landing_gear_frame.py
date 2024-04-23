from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QScrollArea, QFrame

from tabs.geometry.frames.geometry_frame import GeometryFrame, create_line_bar
from utilities import show_popup, Units
from widgets.data_entry_widget import DataEntryWidget


class LandingGearFrame(QWidget, GeometryFrame):
    def __init__(self):
        """Create a frame for entering landing gear data."""
        super(LandingGearFrame, self).__init__()
        self.data_entry_widget: DataEntryWidget | None = None

        self.create_scroll_area()
        self.main_layout.addWidget(QLabel("<b>Landing Gear</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.add_name_layout()

        # List of data labels
        data_units_labels = [
            ("Main Tire Diameter", Units.Length),
            ("Nose Tire Diameter", Units.Length),
            ("Main Strut Length", Units.Length),
            ("Nose Strut Length", Units.Length),
            ("Main Units", Units.Count),
            ("Nose Units", Units.Count),
            ("Main Wheels", Units.Count),
            ("Nose Wheels", Units.Count)
        ]

        # Add the data entry widget to the home layout
        self.data_entry_widget = DataEntryWidget(data_units_labels)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addWidget(create_line_bar())

        self.add_buttons_layout()

        # Adds scroll function
        self.main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def create_scroll_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        self.main_layout = QVBoxLayout(scroll_content)
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout_scroll)

    def add_name_layout(self):
        name_layout = QHBoxLayout()
        spacer_left = QSpacerItem(50, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(200, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_line_edit = QLineEdit(self)
        name_layout.addItem(spacer_left)
        name_layout.addWidget(QLabel("Name: "))
        name_layout.addWidget(self.name_line_edit)
        name_layout.addItem(spacer_right)
        self.main_layout.addLayout(name_layout)

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self):
        """Add the save, delete, and new buttons to the layout."""
        save_button = QPushButton("Save Data", self)
        delete_button = QPushButton("Delete Data", self)
        new_button = QPushButton("New Landing Gear Structure", self)

        save_button.clicked.connect(self.save_data)
        delete_button.clicked.connect(self.delete_data)
        new_button.clicked.connect(self.create_new_structure)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(new_button)
        self.main_layout.addLayout(buttons_layout)

    # noinspection DuplicatedCode
    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data = self.get_data_values()
        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(self.tab_index, self.index, entered_data)
                return
            else:
                self.index = self.save_function(self.tab_index, data=entered_data, new=True)

            show_popup("Data Saved!", self)

    # TODO: Implement proper deletion of data
    def delete_data(self):
        pass

    def create_new_structure(self):
        """Create a new Landing Gear structure."""
        # Clear the main data values
        self.data_entry_widget.clear_values()
        self.name_line_edit.clear()
        self.index = -1

    def get_data_values(self):
        """Retrieve the entered data values from the text fields."""
        data = self.data_entry_widget.get_values()
        data["name"] = self.name_line_edit.text()
        return data

    def load_data(self, data, index):
        """Load the data into the widgets.

        Args:
            data: The data to be loaded into the widgets.
            index: The index of the data in the list.
        """
        self.data_entry_widget.load_data(data)

        self.name_line_edit.setText(data["name"])
        self.index = index
