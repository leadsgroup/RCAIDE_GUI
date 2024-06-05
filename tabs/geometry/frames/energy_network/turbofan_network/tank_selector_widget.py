from PyQt6.QtWidgets import QWidget, QVBoxLayout

from widgets.data_entry_widget import DataEntryWidget
from utilities import Units


class TankSelectorWidget(QWidget):
    def __init__(self, fuel_tank_names):
        super(TankSelectorWidget, self).__init__()
        data_units_labels = []
        for fuel_tank_name in fuel_tank_names:
            data_units_labels.append((fuel_tank_name, Units.Boolean))
        
        self.data_entry_widget = DataEntryWidget(data_units_labels, num_cols=5)
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.data_entry_widget)
        
        self.setLayout(self.main_layout)
