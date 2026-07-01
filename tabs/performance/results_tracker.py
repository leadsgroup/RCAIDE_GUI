# RCAIDE_GUI/tabs/multi_disciplinary/results_tracker.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout,
)
from PyQt6.QtCore import Qt


class ResultsTrackerWidget(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        title = QLabel("Results Summary")
        title.setStyleSheet("font-weight: bold; color: #9fb8ff; font-size: 16px;")
        top_row.addWidget(title)
        top_row.addStretch()

        self.clear_button = QPushButton("Clear")
        self.clear_button.setFixedWidth(70)
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.clicked.connect(self.clear_results)
        top_row.addWidget(self.clear_button)
        layout.addLayout(top_row)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value", "Unit"])
        header = self.table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.setStyleSheet("""
            QWidget {
                background-color: #0a2a2a;
            }
            QTableWidget {
                background-color: #0a2a2a;
                color: #d6e1ff;
                border: 1px solid #1f3a3a;
                gridline-color: #1f3a3a;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #0d3535;
                color: #9fb8ff;
                border: none;
                padding: 6px;
                font-weight: bold;
            }
            QLabel {
                background: transparent;
            }
            QPushButton {
                background-color: #0d3535;
                border: 1px solid #1f3a3a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #9fb8ff;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #144040;
                border-color: #4da3ff;
            }
        """)
        layout.addWidget(self.table)

    def update_results(self, formatted_results):
        self.table.setRowCount(len(formatted_results))
        for row, (label, value, unit) in enumerate(formatted_results):
            self.table.setItem(row, 0, QTableWidgetItem(label))
            val_item = QTableWidgetItem(value)
            val_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, val_item)
            self.table.setItem(row, 2, QTableWidgetItem(unit))

    def clear_results(self):
        self.table.setRowCount(0)
