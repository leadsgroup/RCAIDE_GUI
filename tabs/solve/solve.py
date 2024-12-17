from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
from matplotlib import colormaps

from tabs import TabWidget
import values

from RCAIDE.Framework.Core import Units
# import RCAIDE


class SolveWidget(TabWidget):
    def __init__(self):
        super(SolveWidget, self).__init__()

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        # Create and add a label to the main_layout
        main_layout.addWidget(QLabel("Click Solve Button to View Plots"))

        # Create the Solve button
        solve_button = QPushButton("Solve")
        solve_button.clicked.connect(self.run_solve)

        # Create a scroll area for the plot widgets
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # scroll_area.setFixedSize(1500, 900)  # Set a designated scroll area size

        # Create a container widget for the plots
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)

        # Create two PlotWidgets from PyQtGraph
        self.aircraft_velocity_plot = pg.PlotWidget()
        self.aircraft_altitude_plot = pg.PlotWidget()

        # Set a fixed size for each plot widget
        plot_size = QSize(700, 350)  # Set a fixed plot size
        self.aircraft_velocity_plot.setFixedSize(plot_size)
        self.aircraft_velocity_plot.addLegend()
        self.aircraft_velocity_plot.setLabel('left', 'Velocity', units='kts') 
        self.aircraft_velocity_plot.setLabel('bottom', 'Time', units='mins') 
        self.aircraft_velocity_plot.getAxis('left')
        self.aircraft_velocity_plot.getAxis('bottom')
        self.aircraft_velocity_plot.showGrid(x=True, y=True, alpha=0.3)

        self.aircraft_altitude_plot.setFixedSize(plot_size)
        self.aircraft_altitude_plot.addLegend()
        self.aircraft_altitude_plot.setLabel('left', 'Altitude', units='ft')
        self.aircraft_altitude_plot.setLabel('bottom', 'Time', units='mins')
        self.aircraft_altitude_plot.getAxis('left')
        self.aircraft_altitude_plot.getAxis('bottom')
        self.aircraft_altitude_plot.showGrid(x=True, y=True, alpha=0.3)

        plot_layout.addWidget(self.aircraft_velocity_plot)
        plot_layout.addWidget(self.aircraft_altitude_plot)
        scroll_area.setWidget(plot_container)

        # Add the scroll area to the main_layout
        main_layout.addWidget(scroll_area)

        # Tree layout (on the left)
        self.tree = QTreeWidget()
        self.init_tree()
        tree_layout.addWidget(solve_button)
        tree_layout.addWidget(self.tree)

        # Add layouts to the base_layout
        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(main_layout, 7)

        base_widget = QWidget()
        base_widget.setLayout(base_layout)

        self.setLayout(base_layout)

    def init_tree(self):
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Plot Options", "Enabled"])

        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)

        for category, options in self.plot_options.items():
            category_item = QTreeWidgetItem([category])
            self.tree.addTopLevelItem(category_item)

            for option in options:
                option_item = QTreeWidgetItem([option])
                option_item.setCheckState(
                    1, Qt.CheckState.Checked)  # Initially checked

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
