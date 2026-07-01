# RCAIDE_GUI/tabs/geometry/frames/powertrain/powertrain_frame.py
#
# Created:  Dec 2025, M. Clarke

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------
import RCAIDE
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSpacerItem, QSizePolicy, \
    QPushButton, QComboBox

from tabs.geometry.frames import GeometryFrame
from tabs.geometry.widgets.powertrain.powertrain_widget import PowertrainWidget
from utilities import show_popup, clear_layout, BTN_STYLE


class PowertrainFrame(GeometryFrame):
    """Top-level frame for a single energy network entry in the geometry tree.

    Presents an "Energy Network Type" combo that, when changed, replaces the
    inner ``PowertrainWidget`` with a fresh instance configured for the chosen
    network type (Fuel, Electric, Hybrid, Hydrogen, Fuel Cell).

    ``get_data_values()`` returns the combined GUI data dict and the assembled
    RCAIDE network object.  ``load_data()`` restores a previously saved
    powertrain from a dict in either GUI or native RCAIDE JSON format.
    """

    def __init__(self):
        super(PowertrainFrame, self).__init__()

        self.data_fields = {}
        self.save_function = None
        self.tab_index = -1
        self.index = -1

        # Create a scroll area
        scroll_area = QScrollArea()
        # Allow the widget inside to resize with the scroll area
        scroll_area.setWidgetResizable(True)

        # Create a widget to contain the layout
        scroll_content = QWidget()
        # Set the main layout inside the scroll content
        layout = QVBoxLayout(scroll_content)
        self.powertrain_layout = QVBoxLayout()

        # Create a horizontal layout for the label and buttons
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Powertrain</b>"))

        layout.addLayout(header_layout)
        # Create a horizontal line
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)

        # Add the line bar to the main layout
        layout.addWidget(line_bar)

        self.main_powertrain_widget = self.make_powertrain_widget()
        # Add the grid layout to the home layout
        layout.addWidget(self.main_powertrain_widget)

        layout.addWidget(line_bar)
        layout.addLayout(self.powertrain_layout)

        self.add_buttons_layout()

        # Adds scroll function
        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)

        # Set the main layout of the scroll area
        layout_scroll = QVBoxLayout(self)
        layout_scroll.addWidget(scroll_area)

        # Set the layout to the main window/widget
        self.setLayout(layout_scroll)

    # noinspection PyUnresolvedReferences
    def add_buttons_layout(self):
        # define buttons
        save_button = QPushButton("Save Energy Network Data", self)
        # save_button.setStyleSheet(BTN_STYLE)
        delete_button = QPushButton("Clear Energy Network", self)
        delete_button.setStyleSheet(BTN_STYLE)

        # define action of buttons
        save_button.clicked.connect(self.save_data)
        delete_button.clicked.connect(self.create_new_structure)

        # Create a QHBoxLayout to contain the buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(delete_button)

        self.powertrain_layout.addLayout(buttons_layout)

    def make_powertrain_widget(self):
        """Create a widget for the powertrain section.

        Returns:
            QWidget: The main powertrain widget."""
        main_powertrain_widget = QWidget()
        main_layout = QVBoxLayout()
        type_layout = QHBoxLayout()

        type_layout.addWidget(QLabel("Energy Network Type:"))
        self.powertrain_combo = QComboBox()
        self.powertrain_combo.addItems(["Select Network Type", "Fuel", "Electric", "Hybrid", "Hydrogen", "Fuel Cell"])
        self.powertrain_combo.setFixedWidth(200)
        type_layout.addWidget(self.powertrain_combo)
        type_layout.addStretch()

        self.powertrain_combo.currentIndexChanged.connect(self.display_selected_network)

        main_layout.addLayout(type_layout)
        main_powertrain_widget.setLayout(main_layout)
        return main_powertrain_widget

    def set_save_function(self, function):
        self.save_function = function

    def set_tab_index(self, index):
        self.tab_index = index

    _VALID_NETWORKS = ("Fuel", "Electric", "Hybrid", "Hydrogen", "Fuel Cell")

    def get_data_values(self):
        """Retrieve the entered data values from the widgets."""
        selected_network = self.powertrain_combo.currentText()
        data = {"energy network selected": selected_network}

        if selected_network in self._VALID_NETWORKS:
            item = self.powertrain_layout.itemAt(0)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, PowertrainWidget)
            widget.network_type = selected_network
            data_values, net = widget.get_data_values()

            if isinstance(data_values, bool):
                return False, False

            data["powertrain"] = data_values
        else:
            return False, False

        return data, net

    def create_rcaide_structure(self):
        selected_network = self.powertrain_combo.currentText()
        if selected_network in self._VALID_NETWORKS:
            item = self.powertrain_layout.itemAt(0)
            assert item is not None
            widget = item.widget()
            assert widget is not None and isinstance(widget, PowertrainWidget)
            widget.network_type = selected_network
            _, net = widget.get_data_values()
        else:
            return None

        return net

    def save_data(self):
        """Call the save function and pass the entered data to it."""
        entered_data, component = self.get_data_values()
        if isinstance(entered_data, bool):
            return

        if self.save_function:
            if self.index >= 0:
                self.index = self.save_function(
                    tab_index=self.tab_index, index=self.index, data=entered_data)
                return
            else:
                self.index = self.save_function(
                    tab_index=self.tab_index, vehicle_component=component, data=entered_data, new=True)

        show_popup("Data Saved!", self)

    def load_data(self, data, index):
        """Load the data into the widgets.

        Args:
            data: The data to be loaded into the widgets.
            index: The index of the data in the list.
        """
        self.index = index
        selected_network = data.get("energy network selected", "")
        network_index = self.powertrain_combo.findText(selected_network)
        if network_index != -1:
            self.powertrain_combo.blockSignals(True)
            self.powertrain_combo.setCurrentIndex(network_index)
            self.powertrain_combo.blockSignals(False)

        clear_layout(self.powertrain_layout)

        if selected_network in self._VALID_NETWORKS:
            powertrain_widget = PowertrainWidget()
            powertrain_widget.network_type = selected_network
            self.powertrain_layout.addWidget(powertrain_widget)
            powertrain_widget.load_data_values(data.get("powertrain", {}))

        self.add_buttons_layout()

    def create_new_structure(self):
        """Create a new powertrain structure."""
        while self.powertrain_layout.count():
            item = self.powertrain_layout.takeAt(0)
            assert item is not None

            widget = item.widget()
            assert widget is not None
            widget.deleteLater()

        self.index = -1

    def delete_data(self):
        pass

    def display_selected_network(self, index):
        selected_network = self.powertrain_combo.currentText()
        clear_layout(self.powertrain_layout)

        if selected_network in self._VALID_NETWORKS:
            widget = PowertrainWidget()
            widget.network_type = selected_network
            self.powertrain_layout.addWidget(widget)

        self.add_buttons_layout()
