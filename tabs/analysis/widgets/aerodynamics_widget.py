from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, \
    QComboBox, QSpacerItem, QSizePolicy

from tabs.analysis.widgets import AnalysisWidget
from utilities import create_line_bar, Units, set_data
from widgets.data_entry_widget import DataEntryWidget

import RCAIDE


class AerodynamicsWidget(QWidget, AnalysisWidget):
    analyses = ["Subsonic VLM", "Supersonic VLM"]
    data_units_labels = [
        [
            ("Fuselage Lift Correction", Units.Unitless, "fuselage_lift_correction"),
            ("Trim Drag Correction Factor", Units.Unitless, "trim_drag_correction_factor"),
            ("Wing Parasite Drag Form Factor", Units.Unitless, "wing_parasite_drag_form_factor"),
            ("Fuselage Parasite Drag Form Factor", Units.Unitless, "fuselage_parasite_drag_form_factor"),
            ("Maximum Lift Coefficient Factor", Units.Unitless, "maximum_lift_coefficient_factor"),
            ("Lift-to-Drag Adjustment", Units.Unitless, "lift_to_drag_adjustment"),
            ("Viscous Lift Dependent Drag Factor", Units.Unitless, "viscous_lift_dependent_drag_factor"),
            ("Drag Coefficient Increment", Units.Unitless, "drag_coefficient_increment"),
            ("Spoiler Drag Increment", Units.Unitless, "spoiler_drag_increment"),
            ("Maximum Lift Coefficient", Units.Unitless, "maximum_lift_coefficient"),
            ("Number of Spanwise Vortices", Units.Count, "number_of_spanwise_vortices"),
            ("Number of Chordwise Vortices", Units.Count, "number_of_chordwise_vortices"),
            ("Use Surrogate", Units.Boolean, "use_surrogate"),
            ("Recalculate Total Wetted Area", Units.Boolean, "recalculate_total_wetted_area"),
            ("Propeller Wake Model", Units.Boolean),
            ("Discretize Control Surfaces", Units.Boolean),
            ("Model Fuselage", Units.Boolean),
            ("Model Nacelle", Units.Boolean),
            ("Spanwise Cosine Spacing", Units.Boolean),
            ("Leading Edge Suction Multiplier", Units.Unitless),
            ("Use VORLAX Matrix Calculation", Units.Boolean),
        ],
        [
            ("Fuselage Lift Correction", Units.Unitless, "fuselage_lift_correction"),
            ("Trim Drag Correction Factor", Units.Unitless, "trim_drag_correction_factor"),
            ("Wing Parasite Drag Form Factor", Units.Unitless, "wing_parasite_drag_form_factor"),
            ("Fuselage Parasite Drag Form Factor", Units.Unitless, "fuselage_parasite_drag_form_factor"),
            ("Viscous Lift Dependent Drag Factor", Units.Unitless, "viscous_lift_dependent_drag_factor"),
            ("Lift to Drag Adjustment", Units.Unitless, "lift_to_drag_adjustment"),
            ("Drag Coefficient Increment", Units.Unitless, "drag_coefficient_increment"),
            ("Spoiler Drag Increment", Units.Unitless, "spoiler_drag_increment"),
            ("Oswald Efficiency Factor", Units.Unitless, "oswald_efficiency_factor"),
            ("Span Efficiency", Units.Unitless, "span_efficiency"),
            ("Maximum Lift Coefficient", Units.Unitless, "maximum_lift_coefficient"),
            ("Begin Drag Rise Mach Number", Units.Unitless, "begin_drag_rise_mach_number"),
            ("End Drag Rise Mach Number", Units.Unitless, "end_drag_rise_mach_number"),
            ("Transonic Drag Rise Multiplier", Units.Unitless, "transonic_drag_rise_multiplier"),
            ("Use Surrogate", Units.Boolean, "use_surrogate"),
            ("Propeller Wake Model", Units.Boolean, "propeller_wake_model"),
            ("Model Fuselage", Units.Boolean, "model_fuselage"),
            ("Recalculate Total Wetted Area", Units.Boolean, "recalculate_total_wetted_area"),
            ("Model Nacelle", Units.Boolean, "model_nacelle"),
            ("Discretize Control Surfaces", Units.Boolean, "discretize_control_surfaces"),
            ("Peak Mach Number", Units.Unitless, "peak_mach_number"),
            ("Volume Wave Drag Scaling", Units.Unitless, "volume_wave_drag_scaling"),
            ("Fuselage Parasite Drag Begin Blend Mach", Units.Unitless, "fuselage_parasite_drag_begin_blend_mach"),
            ("Fuselage Parasite Drag End Blend Mach", Units.Unitless, "fuselage_parasite_drag_end_blend_mach"),
            ("Number of Spanwise Vortices", Units.Count, "number_of_spanwise_vortices"),
            ("Number of Chordwise Vortices", Units.Count, "number_of_chordwise_vortices"),
            ("Spanwise Cosine Spacing", Units.Boolean, "spanwise_cosine_spacing"),
            ("Leading Edge Suction Multiplier", Units.Unitless, "leading_edge_suction_multiplier"),
            ("Use VORLAX Matrix Calculation", Units.Boolean, "use_VORLAX_matrix_calculation"),
        ],
    ]

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

    def create_analysis(self):
        analysis_num = self.analysis_selector.currentIndex()
        values_si = self.data_entry_widget.get_values_si()

        if analysis_num == 0:
            aerodynamics = RCAIDE.Framework.Analyses.Aerodynamics.Subsonic_VLM()
        else:
            aerodynamics = RCAIDE.Framework.Analyses.Aerodynamics.Supersonic_VLM()
        
        for data_unit_label in self.data_units_labels[analysis_num]:
            rcaide_label = data_unit_label[-1]
            user_label = data_unit_label[0]

            set_data(aerodynamics, rcaide_label, values_si[user_label])

        return aerodynamics

