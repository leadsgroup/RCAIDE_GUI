import sys

from PyQt6.QtWidgets import QMainWindow, QApplication, QTabWidget

from tabs.analysis import analysis
from tabs.geometry import geometry
from tabs.home import home
from tabs.mission import mission
from tabs.solve import solve


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RCAIDE")

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setMovable(True)

        tabs.addTab(home.get_widget(), "Home")
        tabs.addTab(geometry.get_widget(), "Geometry")
        tabs.addTab(analysis.get_widget(), "Analysis")
        tabs.addTab(mission.get_widget(), "Mission")
        tabs.addTab(solve.get_widget(), "Solve")

 
        self.setCentralWidget(tabs)
        self.resize(800, 450)


app = QApplication(sys.argv)

window = App()
window.show()

app.exec()
