from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

class ImageWidget(QWidget):
    def __init__(self, image_file, w=256, h=256):
        super().__init__()
        
        layout = QVBoxLayout()
        
        pixmap = QPixmap(image_file)
        pixmap_scaled = pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        label = QLabel()
        label.setPixmap(pixmap_scaled)
        # label.setScaledContents(True)
        
        layout.addWidget(label)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(layout)        
    