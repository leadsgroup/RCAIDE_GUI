from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, \
    QComboBox, QSpacerItem, QSizePolicy

from tabs.analysis.widgets import AnalysisWidget
from utilities import create_line_bar, Units
from widgets.data_entry_widget import DataEntryWidget

import RCAIDE


class AerodynamicsWidget(QWidget, AnalysisWidget):
    analyses = ["Subsonic VLM", "Supersonic VLM"]
    data_units_labels = [
        [
            ("Fuselage Lift Correction", Units.Unitless),
            ("Trim Drag Correction Factor", Units.Unitless),
            ("Wing Parasite Drag Form Factor", Units.Unitless),
            ("Fuselage Parasite Drag Form Factor", Units.Unitless),
            ("Maximum Lift Coefficient Factor", Units.Unitless),
            ("Lift-to-Drag Adjustment", Units.Unitless),
            ("Viscous Lift Dependent Drag Factor", Units.Unitless),
            ("Drag Coefficient Increment", Units.Unitless),
            ("Spoiler Drag Increment", Units.Unitless),
            ("Maximum Lift Coefficient", Units.Unitless),
            ("Number of Spanwise Vortices", Units.Count),
            ("Number of Chordwise Vortices", Units.Count),
            ("Use Surrogate", Units.Boolean),
            ("Recalculate Total Wetted Area", Units.Boolean),
            ("Propeller Wake Model", Units.Boolean),
            ("Discretize Control Surfaces", Units.Boolean),
            ("Model Fuselage", Units.Boolean),
            ("Model Nacelle", Units.Boolean),
            ("Spanwise Cosine Spacing", Units.Boolean),
            ("Leading Edge Suction Multiplier", Units.Unitless),
            ("Use VORLAX Matrix Calculation", Units.Boolean),
        ],
        [
            ("Fuselage Lift Correction", Units.Unitless),
            ("Trim Drag Correction Factor", Units.Unitless),
            ("Wing Parasite Drag Form Factor", Units.Unitless),
            ("Fuselage Parasite Drag Form Factor", Units.Unitless),
            ("Viscous Lift Dependent Drag Factor", Units.Unitless),
            ("Lift to Drag Adjustment", Units.Unitless),
            ("Drag Coefficient Increment", Units.Unitless),
            ("Spoiler Drag Increment", Units.Unitless),
            ("Oswald Efficiency Factor", Units.Unitless),
            ("Span Efficiency", Units.Unitless),
            ("Maximum Lift Coefficient", Units.Unitless),
            ("Begin Drag Rise Mach Number", Units.Unitless),
            ("End Drag Rise Mach Number", Units.Unitless),
            ("Transonic Drag Rise Multiplier", Units.Unitless),
            ("Use Surrogate", Units.Boolean),
            ("Propeller Wake Model", Units.Boolean),
            ("Model Fuselage", Units.Boolean),
            ("Recalculate Total Wetted Area", Units.Boolean),
            ("Model Nacelle", Units.Boolean),
            ("Discretize Control Surfaces", Units.Boolean),
            ("Peak Mach Number", Units.Unitless),
            ("Volume Wave Drag Scaling", Units.Unitless),
            ("Fuselage Parasite Drag Begin Blend Mach", Units.Unitless),
            ("Fuselage Parasite Drag End Blend Mach", Units.Unitless),
            ("Number of Spanwise Vortices", Units.Count),
            ("Number of Chordwise Vortices", Units.Count),
            ("Spanwise Cosine Spacing", Units.Boolean),
            ("Leading Edge Suction Multiplier", Units.Unitless),
            ("Use VORLAX Matrix Calculation", Units.Boolean),
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

        settings = aerodynamics.settings
        settings.fuselage_lift_correction = values_si["Fuselage Lift Correction"][0]
        settings.trim_drag_correction_factor = values_si["Trim Drag Correction Factor"][0]
        settings.wing_parasite_drag_form_factor = values_si["Wing Parasite Drag Form Factor"][0]
        settings.fuselage_parasite_drag_form_factor = values_si[
            "Fuselage Parasite Drag Form Factor"]
        settings.lift_to_drag_adjustment = values_si["Lift-to-Drag Adjustment"][0]
        settings.viscous_lift_dependent_drag_factor = values_si[
            "Viscous Lift Dependent Drag Factor"]
        settings.drag_coefficient_increment = values_si["Drag Coefficient Increment"][0]
        settings.spoiler_drag_increment = values_si["Spoiler Drag Increment"][0]
        settings.number_of_spanwise_vortices = values_si["Number of Spanwise Vortices"][0]
        settings.number_of_chordwise_vortices = values_si["Number of Chordwise Vortices"][0]
        settings.use_surrogate = values_si["Use Surrogate"][0]
        settings.recalculate_total_wetted_area = values_si["Recalculate Total Wetted Area"][0]
        settings.propeller_wake_model = values_si["Propeller Wake Model"][0]
        settings.discretize_control_surfaces = values_si["Discretize Control Surfaces"][0]
        settings.model_fuselage = values_si["Model Fuselage"][0]
        settings.model_nacelle = values_si["Model Nacelle"][0]
        settings.spanwise_cosine_spacing = values_si["Spanwise Cosine Spacing"][0]
        settings.leading_edge_suction_multiplier = values_si["Leading Edge Suction Multiplier"][0]
        settings.use_VORLAX_matrix_calculation = values_si["Use VORLAX Matrix Calculation"][0]
        settings.maximum_lift_coefficient = values_si["Maximum Lift Coefficient"][0]

        if analysis_num == 0:
            settings.maximum_lift_coefficient_factor = values_si["Maximum Lift Coefficient Factor"][0]
        elif analysis_num == 1:
            settings.oswald_efficiency_factor = values_si["Oswald Efficiency Factor"][0]
            settings.span_efficiency = values_si["Span Efficiency"][0]
            settings.begin_drag_rise_mach_number = values_si["Begin Drag Rise Mach Number"][0]
            settings.end_drag_rise_mach_number = values_si["End Drag Rise Mach Number"][0]
            settings.transonic_drag_rise_multiplier = values_si["Transonic Drag Rise Multiplier"][0]
            settings.peak_mach_number = values_si["Peak Mach Number"][0]
            settings.volume_wave_drag_scaling = values_si["Volume Wave Drag Scaling"][0]
            settings.fuselage_parasite_drag_begin_blend_mach = values_si[
                "Fuselage Parasite Drag Begin Blend Mach"]
            settings.fuselage_parasite_drag_end_blend_mach = values_si[
                "Fuselage Parasite Drag End Blend Mach"]

        return aerodynamics