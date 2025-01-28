from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTreeWidget, QPushButton,
    QTreeWidgetItem, QHeaderView, QLabel, QDockWidget, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
from matplotlib import colormaps

from tabs import TabWidget
from PyQt6.QtGui import QF
from matplotlib import colormaps

import values

from RCAIDE.Framework.Core import Units

class SolveWidget(TabWidget):
    def __init__(self):
        super().__init__()
        self.main_window = SolveMainWindow()
        
        # layout for main window widget
        layout = QVBoxLayout(self)
        layout.addWidget(self.main_window)
        self.setLayout(layout)

class SolveMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks 
            | QMainWindow.DockOption.AllowTabbedDocks 
            | QMainWindow.DockOption.AnimatedDocks
        )

        self.create_tree_dock()
        self.create_plot_docks()

    def create_tree_dock(self):
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)

        solve_button = QPushButton("Solve")
        solve_button.clicked.connect(self.run_solve)

        self.tree = QTreeWidget()
        self.init_tree()
        tree_layout.addWidget(solve_button)
        tree_layout.addWidget(self.tree)

        self.tree_dock = QDockWidget("Plot Options", self)
        self.tree_dock.setObjectName("plot_options_dock")

        self.tree_dock.setWidget(tree_container)

        self.tree_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tree_dock)

    def create_plot_docks(self):
        global_widget = QWidget()
        global_layout = QVBoxLayout(global_widget)

        label = QLabel("Click Solve Button to View Plots")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        global_layout.addWidget(label)

        #plot_title: label_data
        self.plot_data = {
            "Aircraft Velocity Plot": [('left', 'Velocity', 'kts'),('bottom', 'Time', 'mins')],
            "Aircraft Altitude Plot": [('left', 'Altitude', 'ft'),('bottom', 'Time', 'mins')]
        }

        self.dock_container = QMainWindow()
        self.dock_container.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks |
            QMainWindow.DockOption.AllowTabbedDocks |
            QMainWindow.DockOption.AnimatedDocks
        )   

        self.dock_widgets = []

        for plot_title in self.plot_data:
            plot_widget = pg.PlotWidget()
            plot_widget.setTitle(plot_title)
            plot_widget.addLegend()
            plot_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            first_label,second_label = self.plot_data[plot_title]

            plot_widget.setLabel(first_label[0], first_label[1], units=first_label[2])
            plot_widget.setLabel(second_label[0], second_label[1], units=second_label[2])
            plot_widget.getAxis('left')
            plot_widget.getAxis('bottom')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)

            # Wrap plot in QDockWidget
            dock_widget = QDockWidget(plot_title, self)
            dock_widget.setWidget(plot_widget)
            dock_widget.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable |
                QDockWidget.DockWidgetFeature.DockWidgetFloatable
            )

            self.dock_widgets.append(dock_widget)

        for widget in self.dock_widgets:
            self.dock_container.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, widget)

        # Tabify dock widgets
        for i in range(1, len(self.dock_widgets)):
            self.dock_container.tabifyDockWidget(self.dock_widgets[0], self.dock_widgets[i])

        # set first frame as on load frame
        self.dock_widgets[0].raise_()

        global_layout.addWidget(self.dock_container)

        self.plot_dock = QDockWidget("Configuration Details", self)
        self.plot_dock.setObjectName("config_details_dock")
        self.plot_dock.setWidget(global_widget)

        self.plot_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.plot_dock)

    def init_tree(self):
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Plot Options", "Enabled"])

        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )

        for category, options in self.plot_options.items():
            category_item = QTreeWidgetItem([category])
            self.tree.addTopLevelItem(category_item)

            for option in options:
                option_item = QTreeWidgetItem([option])
                option_item.setCheckState(
                    1, Qt.CheckState.Checked  # Initially checked
                )
                category_item.addChild(option_item)

    def run_solve(self):
        mission = values.rcaide_mission
        print("Starting solve...")
        results = mission.evaluate()
        print("Done with solve")
        cmap = colormaps.get_cmap('plasma')
        num_segments = len(results.segments)
        for i, segment in enumerate(results.segments):
            time = segment.conditions.frames.inertial.time[:, 0] / Units.min
            
            velocity = segment.conditions.freestream.velocity[:, 0] / Units.kts
            altitude = segment.conditions.freestream.altitude[:,0]/Units.feet
            density = segment.conditions.freestream.density[:, 0]
            PR = density / 1.225
            EAS = velocity * np.sqrt(PR)
            mach = segment.conditions.freestream.mach_number[:, 0]
            CAS = EAS * (1+((1/8)*((1-PR)*mach**2)) +
                         ((3/640)*(1-10*PR+(9*PR**2)*(mach**4))))
            
            color = cmap(i / num_segments)
            color_rgba = [int(c * 255) for c in color[:3]]  
            color_hex = pg.mkColor(*color_rgba)  
            
            velocity_pen = pg.mkPen(color=color_hex, width=2)
            velocity_symbol_brush = pg.mkBrush(color=color_hex)
            self.aircraft_velocity_plot.plot(time, velocity, pen=velocity_pen, symbol='o',symbolSize=8,  symbolBrush=velocity_symbol_brush, symbolPen=pg.mkPen(color=color_hex), name=segment.tag.replace('_', ' '))

            altitude_pen = pg.mkPen(color=color_hex, width=2)
            altitude_symbol_brush = pg.mkBrush(color=color_hex)
            self.aircraft_altitude_plot.plot(time, altitude, pen=altitude_pen, symbol='o', symbolSize=8, symbolBrush=altitude_symbol_brush, symbolPen=pg.mkPen(color=color_hex), name=segment.tag.replace('_', ' '))

    plot_options = {
        "Aerodynamics": [
            "Plot Airfoil Boundary Layer Properties",
            "Plot Airfoil Polar Files",
            "Plot Airfoil Polars",
            "Plot Airfoil Surface Forces",
            "Plot Aerodynamic Coefficients",
            "Plot Aerodynamic Forces",
            "Plot Drag Components",
            "Plot Lift Distribution",
            "Plot Rotor Disc Inflow",
            "Plot Rotor Disc Performance",
            "Plot Rotor Performance",
            "Plot Disc and Power Loading",
            "Plot Rotor Conditions",
        ],
        "Energy": [
            "Plot Fuel Consumption",
            "Plot Altitude SFC Weight",
            "Plot Propulsor Throttles",
        ],
        "Mission": [
            "Plot Aircraft Velocities",
            "Plot Flight Conditions",
            "Plot Flight Trajectory",
        ],
        "Stability": [
            "Plot Flight Forces and Moments",
            "Plot Longitudinal Stability",
            "Plot Lateral Stability",
        ],
    }

def get_widget() -> QWidget:
    return SolveWidget()