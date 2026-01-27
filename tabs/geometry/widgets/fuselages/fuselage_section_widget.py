# RCAIDE_GUI/tabs/geometry/widgets/fuselages/fuselage_section_widget.py
# 
# Created:  Dec 2025, M. Clarke 

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
# RCAIDE imports   
import RCAIDE

# RCAIDE GUI imports
from utilities import Units
from widgets import DataEntryWidget

# PyQT imports  
from PyQt6.QtWidgets import QHBoxLayout, QLabel,QLineEdit, QPushButton, QSizePolicy, QSpacerItem,QVBoxLayout, QWidget, QFrame, QComboBox
from PyQt6.QtCore import Qt
# ---------------------------------------------------------------------------------------------------------------------- 
#  Fuselage Section Widget 
# ---------------------------------------------------------------------------------------------------------------------- 
class FuselageSectionWidget(QWidget):
    def __init__(self, index, on_delete, section_data=None):
        super(FuselageSectionWidget, self).__init__()

        # self.data_fields = {}
        self.coordinate_filename = ""
        self.index = index
        self.on_delete = on_delete
        self.data_entry_widget: DataEntryWidget | None = None

        self.name_layout = QHBoxLayout()
        self.init_ui(section_data)

    # noinspection DuplicatedCode
    def init_ui(self, section_data):
        main_layout = QVBoxLayout()
        # add spacing
        spacer_left = QSpacerItem(80, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(300, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.name_layout.addItem(spacer_left)
        self.name_layout.addWidget(QLabel("Segment Name: "))
        self.segment_name_input = QLineEdit(self)
        self.segment_name_input.setFixedWidth(200)
        self.name_layout.addWidget(self.segment_name_input)
        self.name_layout.addItem(spacer_right)

        ## Energy Network
        segment_label = QLabel("Segment Type:")
        segment_label.setFixedWidth(100)  # Adjust width of label
        self.name_layout.addWidget(segment_label) 
        self.fuselage_segment_combo = QComboBox()
        self.fuselage_segment_combo.addItems(["Circle Segment", "Ellipse Segment", "Rounded Rectangle Segment", "Super Ellipse Segment" , "Segment"])
        self.fuselage_segment_combo.setFixedWidth(400)  # Fix width of combo box
        self.name_layout.addWidget(self.fuselage_segment_combo,  alignment=Qt.AlignmentFlag.AlignLeft)
        # Connect signal
        # self.fuselage_segment_combo.currentIndexChanged.connect(self.display_selected_segment)
        

        main_layout.addLayout(self.name_layout)

        # List of data labels
        data_units_labels = [
            ("Percent X Location", Units.Unitless),
            ("Percent Z Location", Units.Unitless),
            ("Height", Units.Length),
            ("Width", Units.Length),
        ]

        self.data_entry_widget = DataEntryWidget(data_units_labels)
        delete_button = QPushButton("Delete Section", self)
        delete_button.setStyleSheet("color:#dbe7ff; font-weight:500; margin:0; padding:0;")
        # delete_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # delete_button.setFixedWidth(150)
        delete_button.clicked.connect(self.delete_button_pressed)
        # center delete button
        delete_button_layout = QHBoxLayout()
        delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        delete_button_layout.addWidget(delete_button)
        delete_button_layout.addItem(QSpacerItem(50, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        main_layout.addWidget(self.data_entry_widget)
        main_layout.addLayout(delete_button_layout)

        # Add horizontal bar
        line_bar = QFrame()
        line_bar.setFrameShape(QFrame.Shape.HLine)
        line_bar.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line_bar)

        self.setLayout(main_layout)

        if section_data:
            self.load_data_values(section_data)

        

    def create_rcaide_structure(self, data): 

        selected_segment = self.fuselage_segment_combo.currentText()
        segment = None

        #if selected_segment == "Ellipse Segment":
            #item = self.powertrain_layout.itemAt(0)
            #assert item is not None
            #widget = item.widget()
            #assert widget is not None and isinstance(widget, PowertrainWidget)
            #_, lines, propulsors,converters = widget.get_data_values()        
           
        if selected_segment == "Circle Segment":
            segment = RCAIDE.Library.Components.Fuselages.Segments.Circle_Segment()
            segment.percent_x_location = data["Percent X Location"][0]
            segment.percent_z_location = data["Percent Z Location"][0]
            segment.height             = data["Height"][0]
            segment.width              = data["Width"][0]
            segment.tag                = data["Segment Name"]
        elif selected_segment == "Ellipse Segment":
            segment = RCAIDE.Library.Components.Fuselages.Segments.Ellipse_Segment()
            segment.percent_x_location = data["Percent X Location"][0]
            segment.percent_z_location = data["Percent Z Location"][0]
            segment.height             = data["Height"][0]
            segment.width              = data["Width"][0]
            segment.tag                = data["Segment Name"]
        elif selected_segment == "Rounded Rectangle Segment":
            segment = RCAIDE.Library.Components.Fuselages.Segments.Rounded_Rectangle_Segment()
            segment.percent_x_location = data["Percent X Location"][0]
            segment.percent_z_location = data["Percent Z Location"][0]
            segment.height             = data["Height"][0]
            segment.width              = data["Width"][0]
            segment.tag                = data["Segment Name"]
        elif selected_segment == "Super Ellipse Segment":
            segment = RCAIDE.Library.Components.Fuselages.Segments.Super_Ellipse_Segment()
            segment.percent_x_location = data["Percent X Location"][0]
            segment.percent_z_location = data["Percent Z Location"][0]
            segment.height             = data["Height"][0]
            segment.width              = data["Width"][0]
            segment.tag                = data["Segment Name"]
        elif selected_segment == "Segment":
            segment = RCAIDE.Library.Components.Fuselages.Segments.Segment()
            segment.percent_x_location = data["Percent X Location"][0]
            segment.percent_z_location = data["Percent Z Location"][0]
            segment.height             = data["Height"][0]
            segment.width              = data["Width"][0]
            segment.tag                = data["Segment Name"]
        else:
            segment = None
        

        return segment

    def get_data_values(self):
        data = self.data_entry_widget.get_values()
        data_si = self.data_entry_widget.get_values_si()
        data["Segment Name"] = self.name_layout.itemAt(2).widget().text()
        data_si["Segment Name"] = self.name_layout.itemAt(2).widget().text()
        selected_type = self.fuselage_segment_combo.currentText()
        data["segment_type"] = selected_type
        data_si["segment_type"] = selected_type
        segment = self.create_rcaide_structure(data_si)
        return data, segment

    def load_data_values(self, section_data):
        self.data_entry_widget.load_data(section_data)
        self.name_layout.itemAt(2).widget().setText(section_data["Segment Name"])

        if "segment_type" in section_data:
            index = self.fuselage_segment_combo.findText(section_data["segment_type"])
            if index>=0:
                self.fuselage_segment_combo.setCurrentIndex(index)

    def delete_button_pressed(self): 
        if self.on_delete is None:
            print("on_delete is None")
            return

        self.on_delete(self.index)
        

    def display_selected_segment(self, index):
        selected_fuselage_segmemt = self.fuselage_segment_combo.currentText()
        # Clear the layout first
        clear_layout(self.powertrain_layout)

        if selected_fuselage_segmemt == "Fuel":
            self.main_powertrain_widget = PowertrainWidget()
            self.powertrain_layout.addWidget(self.main_powertrain_widget)
        elif selected_fuselage_segmemt == "None Selected":
            # Do nothing or add blank widget
            pass
        else:
            # Handle other energy network options here
            pass        
