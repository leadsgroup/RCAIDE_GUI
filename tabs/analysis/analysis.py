from typing import cast

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, \
    QTreeWidgetItem, QScrollArea

from tabs.analysis.widgets import *


class AnalysisWidget(QWidget):

    def __init__(self):
        super(AnalysisWidget, self).__init__()

        options = ["Aerodynamics", "Atmospheric", "Energy",  "Planets", "Weights", 
                        "Propulsion", "Costs", "Noise", "Stability"]

        self.tree_frame = QWidget()
        self.tree_frame_layout = QVBoxLayout(self.tree_frame)
        self.tree_widget = QTreeWidget()
        self.tree_frame_layout.addWidget(self.tree_widget)

        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Analysis", "Enabled"])
        for index, option in enumerate(options):
            item = QTreeWidgetItem([option])
            if index >= 5:
                item.setCheckState(1, Qt.CheckState.Checked)
            else:
                item.setData(1, Qt.ItemDataRole.CheckStateRole,
                             Qt.CheckState.Checked)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)

            self.tree_widget.addTopLevelItem(item)
        
        self.tree_widget.itemChanged.connect(self.handleItemChanged)

        self.base_layout = QHBoxLayout()
        self.base_layout.addWidget(self.tree_frame, 1)

        self.create_scroll_area()
        # Define actions based on the selected index
        self.widgets = [AerodynamicsWidget, AtmosphereWidget, EnergyWidget, PlanetsWidget, WeightsWidget, \
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

    def create_scroll_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        self.main_layout = QVBoxLayout(scroll_content)
        layout_scroll = QVBoxLayout()
        layout_scroll.addWidget(scroll_area)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        self.base_layout.addLayout(layout_scroll, 4)


def get_widget() -> QWidget:
    return AnalysisWidget()
