# RCAIDE_GUI/tabs/solve/solve.py
# 
# Created: Oct 2024, Laboratry for Electric Aircraft Design and Sustainabiltiy

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
from RCAIDE.Framework.Core import Units,  Data
from  RCAIDE.Library.Plots import *  

# PyQT imports 
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QSize
import pyqtgraph as pg

# numpy imports 
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import pickle

# gui imports 
from tabs import TabWidget
import values

# ----------------------------------------------------------------------------------------------------------------------
#  SolveWidget
# ----------------------------------------------------------------------------------------------------------------------  
from RCAIDE.Framework.Core import Units
import RCAIDE


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
        print("Starting solve")
        results = mission.evaluate()
        print("Done with solve")

        styles = {"color": "white", "font-size": "18px"}  
        plot_parameters                  = Data()      
        plot_parameters.line_width       = 5 
        plot_parameters.line_style       = '-'
        plot_parameters.marker_size      = 8
        plot_parameters.legend_font_size = 12
        plot_parameters.axis_font_size   = 14
        plot_parameters.title_font_size  = 18    
        plot_parameters.markers          = ['o', 's', '^', 'X', 'd', 'v', 'P', '>','.', ',', 'o', 'v', '^', '<',\
                                            '>', '1', '2', '3', '4', '8', 's', 'p', '*', 'h'\
                                             , 'H', '+', 'x', 'D', 'd', '|', '_'] 
        plot_parameters.color            = 'black'
        

        line_colors   = cm.inferno(np.linspace(0.2,1,len(results.segments)))
        
        max_velocity = 0
        max_altitude = 0
        for i, segment in enumerate(results.segments):
            # segment settings
            line_width  = plot_parameters.line_width
            rgba_color  = line_colors[i]*255.0   
            segment_tag = segment.tag.replace('_', ' ')
            marker      = plot_parameters.markers[0]
            marker_size =  plot_parameters.marker_size 
            line_color    = (int(rgba_color[0]),int(rgba_color[1]),int(rgba_color[2]))
            line_style    = pg.mkPen(color=line_color, width=line_width)   #  pg.mkPen(color=(255, 0, 0), width=5)
            marker_color  = line_color
            
            # unpack variables 
            time     = segment.conditions.frames.inertial.time[:, 0] / Units.min 
            velocity = segment.conditions.freestream.velocity[:, 0] / Units.kts
            altitude = segment.conditions.freestream.altitude[:,0]/Units.feet
            density  = segment.conditions.freestream.density[:, 0]
            
            # calculate addition variables 
            PR       = density / 1.225
            EAS      = velocity * np.sqrt(PR)
            mach     = segment.conditions.freestream.mach_number[:, 0]
            CAS      = EAS * (1+((1/8)*((1-PR)*mach**2)) +
                         ((3/640)*(1-10*PR+(9*PR**2)*(mach**4))))
            
            
            # aircraft velocity plot
            max_velocity = np.maximum(np.max(velocity),max_velocity)
            self.aircraft_velocity_plot.plot(time, velocity, pen=line_style,  symbol = marker ,  symbolSize=marker_size ,symbolBrush = marker_color,  name=segment_tag)

            # aircraft altitude plot             
            max_altitude = np.maximum(np.max(altitude),max_altitude)
            self.aircraft_altitude_plot.plot(time, altitude, pen=line_style,  symbol = marker , symbolSize= marker_size ,symbolBrush = marker_color ,  name=segment_tag)
            
        
        # aircraft velocity plot settings
        self.aircraft_velocity_plot.setLabel("left", "True Airspeed (kts)", **styles)
        self.aircraft_velocity_plot.setLabel("bottom", "Time (min)", **styles)
        self.aircraft_velocity_plot.showGrid(x=True, y=True) 
        self.aircraft_velocity_plot.addLegend(labelTextSize=plot_parameters.legend_font_size)  
        self.aircraft_velocity_plot.setYRange(0, max_velocity*1.2)

        # aircraft altitude plot settings             
        self.aircraft_altitude_plot.setLabel("left", "True Airspeed (kts)", **styles)
        self.aircraft_altitude_plot.setLabel("bottom", "Time (min)", **styles) 
        self.aircraft_altitude_plot.showGrid(x=True, y=True) 
        self.aircraft_altitude_plot.addLegend(labelTextSize=plot_parameters.legend_font_size)  
        self.aircraft_altitude_plot.setYRange(0, max_altitude*1.2)

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
