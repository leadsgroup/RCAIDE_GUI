from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, \
    QTreeWidgetItem, QHeaderView, QPushButton, QLabel

from tabs.analysis.widgets import *
from tabs import TabWidget
from utilities import create_scroll_area
import values
import RCAIDE

# ============================================================
#  Full Functional Analysis Widget (used by Mission tab)
# ============================================================
class MissionAnalysisWidget(TabWidget):
    def __init__(self):
        super(MissionAnalysisWidget, self).__init__()

        options = [
            "Aerodynamics",
            "Atmospheric",
            "Planets",
            "Weights",
            "Propulsion",
            "Costs",
            "Noise",
            "Stability",
        ]

        self.tree_frame_layout = QVBoxLayout()
        self.tree_widget = QTreeWidget()

        save_analysis_button = QPushButton("Save Analyses")
        save_analysis_button.clicked.connect(self.save_analyses)

        self.tree_frame_layout.addWidget(save_analysis_button)
        self.tree_frame_layout.addWidget(self.tree_widget)

        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Analysis", "Enabled"])
        header = self.tree_widget.header()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        for index, option in enumerate(options):
            item = QTreeWidgetItem([option])
            if index > 3:
                item.setCheckState(1, Qt.CheckState.Unchecked)
            else:
                item.setData(1, Qt.ItemDataRole.CheckStateRole, Qt.CheckState.Checked)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable & ~Qt.ItemFlag.ItemIsEnabled)

            self.tree_widget.addTopLevelItem(item)

        self.tree_widget.itemChanged.connect(self.handleItemChanged)

        self.base_layout = QHBoxLayout()
        self.base_layout.addLayout(self.tree_frame_layout, 1)

        self.main_layout = None
        layout_scroll = create_scroll_area(self, False)
        self.base_layout.addLayout(layout_scroll, 4)

        assert self.main_layout is not None and isinstance(self.main_layout, QVBoxLayout)

        self.analysis_widgets = [
            AerodynamicsWidget,
            AtmosphereWidget,
            PlanetsWidget,
            WeightsWidget,
            PropulsionWidget,
            CostsWidget,
            NoiseWidget,
            StabilityWidget,
        ]
        self.widgets = []

        for index, analysis_widget in enumerate(self.analysis_widgets):
            widget = analysis_widget()
            assert isinstance(widget, AnalysisDataWidget)
            if index >= 4:
                widget.setVisible(False)
            else:
                widget.setVisible(True)

            self.widgets.append(widget)
            self.main_layout.addWidget(widget)

        self.main_layout.addStretch()
        self.main_layout.setSpacing(3)
        self.base_layout.setSpacing(3)
        self.setLayout(self.base_layout)

    # ============================================================
    #  Logic for enabling/disabling sub-analyses
    # ============================================================
    def handleItemChanged(self, item, column):
        if column != 1:
            return

        index = self.tree_widget.indexOfTopLevelItem(item)
        layout_item = self.main_layout.itemAt(index)
        assert layout_item is not None
        widget = layout_item.widget()
        assert widget is not None
        widget.setVisible(item.checkState(1) == Qt.CheckState.Checked)

    def load_from_values(self):
        if not values.analysis_data:
            self.save_analyses()
            return

        for index, widget in enumerate(self.widgets):
            assert isinstance(widget, AnalysisDataWidget)
            widget.load_values(values.analysis_data[index])

        self.save_analyses()

    def get_check_state(self, index) -> bool:
        top_level_item = self.tree_widget.topLevelItem(index)
        assert top_level_item is not None
        return top_level_item.checkState(1) == Qt.CheckState.Checked

    def save_analyses(self):
        if (not getattr(values, "config_data", None) and
                not getattr(values, "rcaide_configs", None)):
            raise RuntimeError(
                "No aircraft configuration data found. "
                "Create a configuration in the Aircraft Configs tab."
            )
        if (not getattr(values, "rcaide_configs", None) or
                not values.rcaide_configs):
            from tabs.aircraft_configs.aircraft_configs import build_rcaide_configs_from_geometry
            try:
                values.rcaide_configs = build_rcaide_configs_from_geometry()
            except Exception as exc:
                raise RuntimeError(
                    "No RCAIDE configurations found. "
                    "Save a configuration in the Aircraft Configs tab."
                ) from exc
        values.analysis_data = []
        values.rcaide_analyses = {}

        for tag, config in values.rcaide_configs.items():

            analysis = RCAIDE.Framework.Analyses.Vehicle()
            geometry = RCAIDE.Framework.Analyses.Geometry.Geometry()
            geometry.vehicle = config
            analysis.append(geometry)

            for index, widget in enumerate(self.widgets):
                assert isinstance(widget, AnalysisDataWidget)

                if self.get_check_state(index):
                    analysis.append(widget.create_analysis(config))

            energy = RCAIDE.Framework.Analyses.Energy.Energy()
            energy.vehicle = config
            analysis.append(energy)

            values.rcaide_analyses[tag] = analysis
            values.analysis_data.append(analysis)
