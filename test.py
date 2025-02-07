from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk

import sys

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RCAIDE GUI")
        base_layout = QHBoxLayout()
        
        self.vtkWidget = QVTKRenderWindowInteractor()
        base_layout.addWidget(self.vtkWidget)
        
        renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(renderer)
        render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        render_window_interactor.Initialize()
        render_window_interactor.Start()
        self.setLayout(base_layout)


app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec())