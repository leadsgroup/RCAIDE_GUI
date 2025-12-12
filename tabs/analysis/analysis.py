from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, \
    QTreeWidgetItem, QHeaderView, QPushButton, QLabel

from tabs.analysis.widgets import *
from tabs import TabWidget
from utilities import create_scroll_area
import values
import RCAIDE

# ============================================================
#  Work-in-Progress Placeholder (shown in Analysis tab)
# ============================================================
class AnalysisWidget(TabWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("🚧 Work in Progress 🚧\n\nThis page is under construction.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #e5f0ff;
                font-size: 18px;
                font-weight: bold;
                background-color: #0d1522;
                border: 1px solid #2d3a4e;
                border-radius: 8px;
                padding: 50px;
            }
        """)
        layout.addWidget(label)


# ============================================================
#  Factory for Analysis tab
# ============================================================
def get_widget() -> QWidget:
    return AnalysisWidget()
