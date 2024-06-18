from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, \
    QComboBox, QSpacerItem, QSizePolicy

from utilities import create_line_bar, Units
from widgets.data_entry_widget import DataEntryWidget


class AerodynamicsWidget(QWidget):
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
            ("Number of Spanwise Vortices", Units.Count),
            ("Number of Chordwise Vortices", Units.Count),
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
        self.data_values = {}
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(QLabel("<b>Aerodynamics</b>"))
        self.main_layout.addWidget(create_line_bar())

        analysis_selector = QComboBox()
        analysis_selector.addItems(self.analyses)
        analysis_selector.currentIndexChanged.connect(self.on_analysis_change)
        self.main_layout.addWidget(analysis_selector)

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
