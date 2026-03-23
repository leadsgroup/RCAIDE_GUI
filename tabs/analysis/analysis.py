from PyQt6.QtCore import Qt, QTimer
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

        self.save_notice = QLabel("")
        self.save_notice.setVisible(False)
        self.save_notice.setStyleSheet(
            "color:#10351e; background:#9fe3b5; border:1px solid #2d8a57; "
            "border-radius:4px; padding:6px 10px; font-weight:600;"
        )
        analyses_v.addWidget(self.save_notice)

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
        # Build the RCAIDE analyses from the current UI state and store them in `values`.
        self.analysis_content.save_analyses()
        saved_configs = list(getattr(values, "rcaide_analyses", {}).keys())
        # Show a short in-app confirmation so the user does not have to rely on terminal output.
        self.save_notice.setText(
            f"Analyses saved successfully for {len(saved_configs)} configuration(s)."
        )
        self.save_notice.setVisible(True)
        QTimer.singleShot(2500, lambda: self.save_notice.setVisible(False))

        # Print a readable summary of what was written into `values.rcaide_analyses`.
        print("\n[Analyses Saved]")
        print(f"Configs: {len(saved_configs)}")
        print(f"Names: {', '.join(saved_configs) if saved_configs else 'None'}")

        for config_name, analysis in getattr(values, "rcaide_analyses", {}).items():
            try:
                entries = list(analysis)
            except TypeError:
                entries = []

            entry_labels = [
                getattr(entry, "tag", entry.__class__.__name__)
                for entry in entries
            ]
            print(f"- {config_name}")
            print(f"  Entries: {len(entry_labels)}")
            print(f"  Tags: {', '.join(entry_labels) if entry_labels else 'None'}")

    def load_from_values(self):
        if hasattr(self.analysis_content, "load_values"):
            self.analysis_content.load_values()

    def get_data(self):
        return self.analysis_content.get_data()
    
def get_widget() -> QWidget:
    return AnalysisWidget()
