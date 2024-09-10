from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, \
    QTreeWidgetItem, QHeaderView

from tabs.analysis.widgets import *
from tabs import TabWidget
from utilities import create_scroll_area
import values

import RCAIDE


class AnalysisWidget(TabWidget):
    def __init__(self):
        super(AnalysisWidget, self).__init__()

        options = ["Aerodynamics", "Atmospheric", "Planets", "Weights",
                   "Propulsion", "Costs", "Noise", "Stability"]

        self.tree_frame_layout = QVBoxLayout()
        self.tree_widget = QTreeWidget()
        self.tree_frame_layout.addWidget(self.tree_widget)

        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Analysis", "Enabled"])
        self.tree_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        for index, option in enumerate(options):
            item = QTreeWidgetItem([option])
            if index >= 4:
                item.setCheckState(1, Qt.CheckState.Checked)
            else:
                item.setData(1, Qt.ItemDataRole.CheckStateRole,
                             Qt.CheckState.Checked)
                item.setFlags(
                    item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable & ~Qt.ItemFlag.ItemIsEnabled)

            self.tree_widget.addTopLevelItem(item)

        self.tree_widget.itemChanged.connect(self.handleItemChanged)

        self.base_layout = QHBoxLayout()
        self.base_layout.addLayout(self.tree_frame_layout, 1)

        self.main_layout = None
        layout_scroll = create_scroll_area(self, False)
        self.base_layout.addLayout(layout_scroll, 4)

        assert self.main_layout is not None and isinstance(
            self.main_layout, QVBoxLayout)
        # Define actions based on the selected
        self.widgets = [AerodynamicsWidget, AtmosphereWidget, PlanetsWidget, WeightsWidget,
                        PropulsionWidget, CostsWidget, NoiseWidget, StabilityWidget]

        for widget in self.widgets:
            self.main_layout.addWidget(widget())

        self.main_layout.setSpacing(3)
        self.base_layout.setSpacing(3)

        self.setLayout(self.base_layout)

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
        pass

    def save_analyses(self):
        for tag, config in values.rcaide_configs.items():
            analysis = RCAIDE.Framework.Analyses.Vehicle()
            for widget in self.widgets:
                assert isinstance(widget, AnalysisDataWidget)
                analysis.append(widget.create_analysis(config))

            values.rcaide_analyses[tag] = analysis


def get_widget() -> QWidget:
    return AnalysisWidget()
