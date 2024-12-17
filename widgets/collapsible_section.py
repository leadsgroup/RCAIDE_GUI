from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QScrollArea
)
from PyQt6.QtCore import Qt, QSize

class CollapsibleSection(QWidget):
    def __init__(self, title: str, content_widget: QWidget):
        super().__init__()

        # Main layout for the collapsible section
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Header layout with toggle button and title
        header_layout = QHBoxLayout()
        self.toggle_button = QToolButton()
        self.toggle_button.setIconSize(QSize(10, 10))

        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        self.toggle_button.clicked.connect(self.toggle_content)

        header_label = QLabel(f"<b>{title}</b>")
        header_label.setStyleSheet("font-weight: bold;")

        header_layout.addWidget(self.toggle_button)
        header_layout.addWidget(header_label)

        self.main_layout.addLayout(header_layout)

        # Content widget setup
        self.content_widget = content_widget

        self.content_container = content_widget
        self.main_layout.addWidget(self.content_container)

        # Start in expanded state
        self.is_expanded = True

        # Show content by default
        self.content_container.show()  
    
    def toggle_content(self):
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.content_container.show()
            self.toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        else:
            self.content_container.hide()
            self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
    