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
        print("Index changed to", index)

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

            set_data(aerodynamics, rcaide_label, values_si[user_label])

        aerodynamics.geometry = vehicle
        return aerodynamics
    
    def get_values(self):
        return self.data_entry_widget.get_values()
    
    def load_values(self, values):
        super().load_values(values)
        self.data_entry_widget.load_data(values)

    analyses = ["Vortex Lattice Method"]
    data_units_labels = [
        [
            ("Fuselage Lift Correction", Units.Unitless, "fuselage_lift_correction"),
            ("Trim Drag Correction Factor", Units.Unitless,
             "trim_drag_correction_factor"),
            ("Wing Parasite Drag Form Factor", Units.Unitless,
             "wing_parasite_drag_form_factor"),
            ("Fuselage Parasite Drag Form Factor", Units.Unitless,
             "fuselage_parasite_drag_form_factor"),
            ("Maximum Lift Coefficient Factor", Units.Unitless,
             "maximum_lift_coefficient_factor"),
            ("Lift-to-Drag Adjustment", Units.Unitless, "lift_to_drag_adjustment"),
            ("Viscous Lift Dependent Drag Factor", Units.Unitless,
             "viscous_lift_dependent_drag_factor"),
            ("Drag Coefficient Increment", Units.Unitless,
             "drag_coefficient_increment"),
            ("Spoiler Drag Increment", Units.Unitless, "spoiler_drag_increment"),
            ("Maximum Lift Coefficient", Units.Unitless, "maximum_lift_coefficient"),
            ("Number of Spanwise Vortices", Units.Count,
             "number_of_spanwise_vortices"),
            ("Number of Chordwise Vortices", Units.Count,
             "number_of_chordwise_vortices"),
            ("Use Surrogate", Units.Boolean, "use_surrogate"),
            ("Recalculate Total Wetted Area", Units.Boolean,
             "recalculate_total_wetted_area"),
            ("Propeller Wake Model", Units.Boolean, "propeller_wake_model"),
            ("Discretize Control Surfaces", Units.Boolean,
             "discretize_control_surfaces"),
            ("Model Fuselage", Units.Boolean, "model_fuselage"),
            ("Trim Aircraft", Units.Boolean, "trim_aircraft"),
            ("Spanwise Cosine Spacing", Units.Boolean, "spanwise_cosine_spacing"),
            ("Leading Edge Suction Multiplier", Units.Unitless,
             "leading_edge_suction_multiplier"),
            ("Use VORLAX Matrix Calculation", Units.Boolean,
             "use_VORLAX_matrix_calculation"),
            ("Supersonic Peak Mach Number", Units.Unitless,
             "supersonic.peak_mach_number"),
            ("Supersonic Begin Drag Rise Mach Number", Units.Unitless,
             "supersonic.begin_drag_rise_mach_number"),
            ("Supersonic End Drag Rise Mach Number", Units.Unitless,
             "supersonic.end_drag_rise_mach_number"),
            ("Supersonic Transonic Drag Multiplier", Units.Unitless,
             "supersonic.transonic_drag_multiplier"),
            ("Supersonic Volume Wave Drag Scaling", Units.Unitless,
             "supersonic.volume_wave_drag_scaling"),
            ("Supersonic Fuselage Parasite Drag Begin Blend Mach", Units.Unitless,
             "supersonic.fuselage_parasite_drag_begin_blend_mach"),
            ("Supersonic Fuselage Parasite Drag End Blend Mach",
             Units.Unitless, "supersonic.fuselage_parasite_drag_end_blend_mach")
        ]
    ]
