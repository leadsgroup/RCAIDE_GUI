import json
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, \
    QComboBox

from tabs.analysis.widgets import AnalysisDataWidget
from utilities import create_line_bar, create_scroll_area, Units, set_data
from widgets.data_entry_widget import DataEntryWidget

import RCAIDE 

class AerodynamicsWidget(AnalysisDataWidget):
    def __init__(self):
        super(AerodynamicsWidget, self).__init__()
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(QLabel("<b>Aerodynamics</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems(self.analyses)
        self.analysis_selector.currentIndexChanged.connect(
            self.on_analysis_change)
        self.main_layout.addWidget(self.analysis_selector)

        self.data_entry_widget = DataEntryWidget(self.data_units_labels[0])

        # Load defaults
        with open("app_data/defaults/aerodynamic_analysis.json", "r") as defaults:
            self.defaults = json.load(defaults)

        self.data_entry_widget.load_data(self.defaults)
        self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.addWidget(create_line_bar())

        self.setLayout(self.main_layout)

        # Adds scroll function
        # self.main_layout.addItem(QSpacerItem(
        #     20, 40, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding))

    def on_analysis_change(self, index): 
        assert self.main_layout is not None

        self.main_layout.removeWidget(self.data_entry_widget)
        self.data_entry_widget = DataEntryWidget(self.data_units_labels[index])
        self.data_entry_widget.load_data(self.defaults[1])
        # self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.insertWidget(
            self.main_layout.count() - 1, self.data_entry_widget)

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

    def create_analysis(self, vehicle: RCAIDE.Vehicle):
        analysis_num = self.analysis_selector.currentIndex()
        values_si = self.data_entry_widget.get_values_si()

        if analysis_num == 0:
            aerodynamics = RCAIDE.Framework.Analyses.Aerodynamics.Vortex_Lattice_Method()

        for data_unit_label in self.data_units_labels[analysis_num]:
            rcaide_label = data_unit_label[-1]
            user_label = data_unit_label[0]
            set_data(aerodynamics.settings, rcaide_label, values_si[user_label][0])

        aerodynamics.vehicle = vehicle
        return aerodynamics
    
    def get_values(self):
        return self.data_entry_widget.get_values()
    
    def load_values(self, values):
        super().load_values(values)
        self.data_entry_widget.load_data(values)

    analyses = ["Vortex Lattice Method"]
    data_units_labels = [
        [
            ("Propeller Wake Model", Units.Boolean, "propeller_wake_model"),
            ("Model Fuselage", Units.Boolean, "model_fuselage"),
            ("Number of Spanwise Vortices", Units.Count, "number_of_spanwise_vortices"),
            ("Number of Chordwise Vortices", Units.Count, "number_of_chordwise_vortices"),
            ("Wing Spanwise Vortices", Units.Unitless, "wing_spanwise_vortices"),
            ("Wing Chordwise Vortices", Units.Count, "wing_chordwise_vortices"),
            ("Fuselage Spanwise Vortices", Units.Count, "fuselage_spanwise_vortices"),
            ("Fuselage Chordwise Vortices", Units.Count, "fuselage_chordwise_vortices"),
            ("Spanwise Cosine Spacing", Units.Boolean, "spanwise_cosine_spacing"),
            ("Vortex Distribution", Units.Unitless, "vortex_distribution"),
            ("Leading Edge Suction Multiplier", Units.Unitless, "leading_edge_suction_multiplier"),
            ("Use VORLAX Matrix Calculation", Units.Boolean, "use_VORLAX_matrix_calculation"),
            ("Floating Point Precision", Units.Unitless, "floating_point_precision"),

        ]
    ]
