# RCAIDE_GUI/tabs/solve/solve.py
# 
# Created: Oct 2024, Laboratry for Electric Aircraft Design and Sustainabiltiy

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
from RCAIDE.Framework.Core import Units,  Data
from RCAIDE.Library.Plots import *  

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
from .plots.create_plot_widgets import create_plot_widgets
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

        plot_size = QSize(700, 400)  # Set a fixed plot size
        show_legend = True
        create_plot_widgets(self,plot_layout,plot_size,show_legend) 

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
        print("Commencing Mission Simulation")
        results = mission.evaluate()
        print("Completed Mission Simulation")
        
        
        
        # WE NEED TO MAKE THESE OPTIONS 

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
        

        line_colors   = cm.viridis(np.linspace(0.2,1,len(results.segments)))
        
        # REPEAT FOR OTHER PLOTS 
        plot_aircraft_velocities_flag = True
        show_grid =  True
        save_figure = False 
        if plot_aircraft_velocities_flag == True:
            plot_aircraft_velocities(self, results,line_colors, styles, plot_parameters, show_grid, save_figure)
         

    plot_options = {
        "Aerodynamics": [
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
