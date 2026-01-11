import RCAIDE
from PyQt6.QtWidgets import (QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget, QFrame)

from utilities import Units, clear_layout
from widgets import DataEntryWidget
from tabs.geometry.widgets.fuselages.cabin_class_widget import CabinClassWidget


class CabinWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None, cabin_type="Regular"):
        super(CabinWidget, self).__init__()
        self.index = index
        self.on_delete = on_delete
        self.cabin_type = cabin_type
        self.data_entry_widget: DataEntryWidget | None = None
        self.name_layout = QHBoxLayout()
        self.classes_layout = QVBoxLayout()
        self.init_ui(section_data)

    # noinspection DuplicatedCode
    def init_ui(self, section_data):
        main_layout = QVBoxLayout()
        type_label = QLabel(f"<b>Type: {self.cabin_type} Cabin</b>")
        main_layout.addWidget(type_label)
        # add spacing
        spacer_left = QSpacerItem(80, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(300, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_layout.addItem(spacer_left)
        self.name_layout.addWidget(QLabel("Cabin Name: "))
        self.name_layout.addWidget(QLineEdit(self))
        self.name_layout.addItem(spacer_right)

        main_layout.addLayout(self.name_layout)

        # List of data labels
        data_units_labels = [
            ("Number of Passengers", Units.Count),
            ("Number of Seats", Units.Count),
            ("Type A Door Length", Units.Length),
            ("Galley Lavatory Length", Units.Length),
            ("Emergency Exit Seat Pitch", Units.Length),
            ("Length", Units.Length),
            ("Width", Units.Length),
            ("Height", Units.Length),
            ("Wide Body", Units.Boolean)
            #potentially add the "filled seats arrangement" option later
        ]

        self.data_entry_widget = DataEntryWidget(data_units_labels)
        main_layout.addWidget(self.data_entry_widget)

        main_layout.addWidget(QLabel("<b>Cabin Classes</b>"))
        add_class_button = QPushButton("Add Cabin Class")
        add_class_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        add_class_button.clicked.connect(self.add_cabin_class)
        main_layout.addWidget(add_class_button)
        main_layout.addLayout(self.classes_layout)

        # Add horizontal bar
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line_bar)

        delete_button = QPushButton("Delete Cabin", self)
        delete_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        delete_button.clicked.connect(self.delete_button_pressed)
        # center delete button
        delete_button_layout = QHBoxLayout()
        delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        delete_button_layout.addWidget(delete_button)
        delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        main_layout.addLayout(delete_button_layout)

        self.setLayout(main_layout)

        if section_data:
            self.load_data_values(section_data)

        

    def add_cabin_class(self):
        widget = CabinClassWidget(self.classes_layout.count(), self.delete_cabin_class)
        self.classes_layout.addWidget(widget)

    def delete_cabin_class(self, index):
        item = self.classes_layout.itemAt(index)
        if item:
            widget = item.widget()
            if widget:
                widget.deleteLater()
                self.classes_layout.removeWidget(widget)
        self.classes_layout.update()
        for i in range(self.classes_layout.count()):
            item = self.classes_layout.itemAt(i)
            if item and item.widget():
                item.widget().index = i

    def create_rcaide_structure(self, data):
        if self.cabin_type == "Side":
            cabin = RCAIDE.Library.Components.Fuselages.Cabins.Side_Cabin()
            
        else:
            cabin = RCAIDE.Library.Components.Fuselages.Cabins.Cabin()

        cabin.tag = data["Cabin Name"]
        cabin.number_of_passengers = int(data["Number of Passengers"][0])
        cabin.number_of_seats = int(data["Number of Seats"][0])
        cabin.type_a_door_length = data["Type A Door Length"][0]
        cabin.galley_lavatory_length = data["Galley Lavatory Length"][0]
        cabin.emergency_exit_seat_pitch = data["Emergency Exit Seat Pitch"][0]
        cabin.length = data["Length"][0]
        cabin.width = data["Width"][0]
        cabin.height = data["Height"][0]
        cabin.wide_body = data["Wide Body"][0]

        return cabin

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data["Cabin Name"] = self.name_layout.itemAt(2).widget().text()
        data["cabin_type"] = self.cabin_type
        data_si["Cabin Name"] = self.name_layout.itemAt(2).widget().text()
        cabin_object = self.create_rcaide_structure(data_si)

        data["classes"] = []
        for i in range(self.classes_layout.count()):
            item = self.classes_layout.itemAt(i)
            if item and item.widget():
                class_widget = item.widget()
                class_data, class_object = class_widget.get_data_values()
                data["classes"].append(class_data)
                if hasattr(cabin_object, "append_cabin_class"):
                    cabin_object.append_cabin_class(class_object)
                else:
                    cabin_object.classes.append(class_object)

        return data, cabin_object

    def load_data_values(self, section_data):
        self.data_entry_widget.load_data(section_data)
        self.name_layout.itemAt(2).widget().setText(section_data["Cabin Name"])
        if "cabin_type" in section_data:
            self.cabin_type = section_data["cabin_type"]
            self.layout().itemAt(0).widget().setText(f"<b>Type: {self.cabin_type} Cabin</b>")
        clear_layout(self.classes_layout)
        if "classes" in section_data:   
            for class_data in section_data["classes"]:
                class_widget = CabinClassWidget(self.classes_layout.count(), self.delete_cabin_class, class_data)
                self.classes_layout.addWidget(class_widget)

    def delete_button_pressed(self):
        if self.on_delete:
            self.on_delete(self.index)
