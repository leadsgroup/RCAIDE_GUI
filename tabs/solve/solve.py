from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QSize
import pyqtgraph as pg
import numpy as np

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
        plot_size = QSize(700, 400)  # Set a fixed plot size
        self.aircraft_velocity_plot.setFixedSize(plot_size)
        self.aircraft_velocity_plot.addLegend()
        
        self.aircraft_altitude_plot.setFixedSize(plot_size)
        self.aircraft_altitude_plot.addLegend()

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
        for segment in results.segments:
            time = segment.conditions.frames.inertial.time[:, 0] / Units.min
            
            velocity = segment.conditions.freestream.velocity[:, 0] / Units.kts
            altitude = segment.conditions.freestream.altitude[:,0]/Units.feet
            density = segment.conditions.freestream.density[:, 0]
            PR = density / 1.225
            EAS = velocity * np.sqrt(PR)
            mach = segment.conditions.freestream.mach_number[:, 0]
            CAS = EAS * (1+((1/8)*((1-PR)*mach**2)) +
                         ((3/640)*(1-10*PR+(9*PR**2)*(mach**4))))
            
            blue_pen = pg.mkPen(color=(0, 0, 255), width=5)
            red_pen = pg.mkPen(color=(255, 0, 0), width=5)
            self.aircraft_velocity_plot.plot(time, velocity, pen=blue_pen, name=segment.tag.replace('_', ' '))
            self.aircraft_altitude_plot.plot(time, altitude, pen=red_pen, name=segment.tag.replace('_', ' '))

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
