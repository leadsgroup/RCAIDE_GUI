import RCAIDE
from PyQt6.QtWidgets import (QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget, QFrame, QComboBox)

from utilities import Units
from widgets import DataEntryWidget


class CabinClassWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None):
        super().__init__()
        self.index = index
        self.on_delete = on_delete
        self.data_entry_widget: DataEntryWidget | None = None
        self.header_layout = QHBoxLayout()
        self.init_ui(section_data)

    # noinspection DuplicatedCode
    def init_ui(self, section_data):
        main_layout = QVBoxLayout()
        # add spacing
        spacer_left = QSpacerItem(80, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.header_layout.addItem(spacer_left)
        self.header_layout.addWidget(QLabel("Class Type: "))
        self.class_type_combo = QComboBox()
        self.class_type_combo.addItems(["Economy", "Business", "First"])
        self.header_layout.addWidget(self.class_type_combo)
        self.header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        delete_btn = QPushButton("Delete Class")
        delete_btn.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        delete_btn.clicked.connect(self.delete_clicked)
        self.header_layout.addWidget(delete_btn)
        main_layout.addLayout(self.header_layout)

        # List of data labels
        self.data_units_labels = [
            ("Number of Passengers", Units.Count),
            ("Number of Seats Abreast", Units.Count),
            ("Number of Rows", Units.Count),
            ("Number of Seats", Units.Count),
            ("Seat Width", Units.Length),
            ("Seat Arm Rest Width", Units.Length),
            ("Seat Length", Units.Length),
            ("Seat Pitch", Units.Length),
            ("Aisle Width", Units.Length)
        ]

        self.data_entry_widget = DataEntryWidget(self.data_units_labels)
      
        main_layout.addWidget(self.data_entry_widget)

        # Add horizontal bar
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line_bar)

        if section_data:
            self.load_data_values(section_data)

        self.setLayout(main_layout)

    def create_rcaide_structure(self, data):
        class_type = data.get("class_type", self.class_type_combo.currentText())
        if class_type == "Economy":
            classtype = RCAIDE.Library.Components.Fuselages.Cabins.Classes.Economy()
        elif class_type == "Business":
            classtype = RCAIDE.Library.Components.Fuselages.Cabins.Classes.Business()
        elif class_type == "First":
            classtype = RCAIDE.Library.Components.Fuselages.Cabins.Classes.First()
        else:
            classtype = RCAIDE.Library.Components.Fuselages.Cabins.Classes.Economy()
            #economy is default

        classtype.number_of_passengers = int(data["Number of Passengers"][0])
        classtype.number_of_seats_abreast = int(data["Number of Seats Abreast"][0])
        classtype.number_of_rows = int(data["Number of Rows"][0])
        classtype.number_of_seats = int(data["Number of Seats"][0])
        classtype.seat_width = data["Seat Width"][0]
        classtype.seat_arm_rest_width = data["Seat Arm Rest Width"][0]
        classtype.seat_length = data["Seat Length"][0]
        classtype.seat_pitch = data["Seat Pitch"][0]
        classtype.aisle_width = data["Aisle Width"][0]

        return classtype

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        selected_type = self.class_type_combo.currentText()
        data_si["class_type"] = selected_type
        data["class_type"] = selected_type
        classtype = self.create_rcaide_structure(data_si)
        return data, classtype

    def load_data_values(self, section_data):
        self.data_entry_widget.load_data(section_data)
        if "class_type" in section_data:
            self.class_type_combo.setCurrentText(section_data["class_type"])

    def delete_clicked(self):
        if self.on_delete:
            self.on_delete(self.index)
