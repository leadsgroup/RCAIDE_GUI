from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel
from widgets.animated_toggle import AnimatedToggle
import qdarktheme

class ThemeSwitch(QMainWindow):
    
    
    def __init__(self):
        super().__init__()

        qdarktheme.setup_theme("dark")
    
    def light_theme(self):

            qdarktheme.setup_theme("light")

    def dark_theme(self):
        
            qdarktheme.setup_theme("dark")