from PyQt6.QtWidgets import QWidget, QVBoxLayout

from utilities import Units
from widgets import DataEntryWidget


class TankSelectorWidget(QWidget):
    def __init__(self, fuel_tank_names, name):
        super(TankSelectorWidget, self).__init__()
        data_units_labels = []
        for fuel_tank_name in fuel_tank_names:
            data_units_labels.append((fuel_tank_name, Units.Boolean))

        self.data_entry_widget = DataEntryWidget(data_units_labels, num_cols=5)
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.data_entry_widget)
        self.fuel_tank_names = fuel_tank_names
        self.name = name

        self.setLayout(self.main_layout)

    def get_selected_tanks(self):
        selected_tanks = self.data_entry_widget.get_values()
        selected_tank_names = []
        for name, selected in selected_tanks.items():
            if selected:
                selected_tank_names.append(name)

        return selected_tank_names
