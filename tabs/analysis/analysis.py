from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, \
    QTreeWidgetItem, QHeaderView, QPushButton, QLabel, QGroupBox
from tabs.mission.widgets import MissionAnalysisWidget
from tabs.analysis.widgets import *
from tabs import TabWidget
from utilities import create_scroll_area
import values
import RCAIDE


class AnalysisWidget(TabWidget):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        analyses_box = QGroupBox("Analyses Setup")
        analyses_v = QVBoxLayout(analyses_box)

        self.analysis_content = MissionAnalysisWidget()
        analyses_v.addWidget(self.analysis_content)

        layout.addWidget(analyses_box)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save Analyses")
        self.save_btn.setStyleSheet("background-color:#141b29; color:#e5f0ff; padding: 8px;")
        self.save_btn.clicked.connect(self.save_analyses_to_values)
        
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        
        layout.addLayout(btn_row)

    def save_analyses_to_values(self):
        self.analysis_content.save_analyses()
        print("Analyses saved to values.")

    def load_from_values(self):
        if hasattr(self.analysis_content, "load_values"):
            self.analysis_content.load_values()

    def get_data(self):
        return self.analysis_content.get_data()
    
def get_widget() -> QWidget:
    return AnalysisWidget()
