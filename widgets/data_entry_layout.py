from PyQt6.QtWidgets import QLayout


class DataEntryLayout(QLayout):
    def __init__(self, data_units_labels):
        super(DataEntryLayout, self).__init__()
        self.data_units_labels = data_units_labels
