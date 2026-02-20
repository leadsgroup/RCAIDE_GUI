# RCAIDE_GUI/tabs/solve/plots/create_plot_widgets.py
# 
# Created: Oct 2024, Laboratry for Electric Aircraft Design and Sustainabiltiy

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------  
# PyQT imports  
import pyqtgraph as pg
 
def create_plot_widgets(self,plot_layout, plot_size,show_legend):
     
    # Create two PlotWidgets from PyQtGraph
    self.aircraft_TAS_plot  = pg.PlotWidget()
    self.aircraft_EAS_plot  = pg.PlotWidget()
    self.aircraft_Mach_plot = pg.PlotWidget()
    self.aircraft_CAS_plot  = pg.PlotWidget()

    # Set a fixed size for each plot widget
    self.aircraft_TAS_plot.setFixedSize(plot_size)
    self.aircraft_EAS_plot.setFixedSize(plot_size)
    self.aircraft_Mach_plot.setFixedSize(plot_size)
    self.aircraft_CAS_plot.setFixedSize(plot_size)
    
    if show_legend:
        self.aircraft_TAS_plot.addLegend() 
        self.aircraft_EAS_plot.addLegend() 
        self.aircraft_Mach_plot.addLegend() 
        self.aircraft_CAS_plot.addLegend() 

    plot_layout.addWidget(self.aircraft_TAS_plot)
    plot_layout.addWidget(self.aircraft_EAS_plot)
    plot_layout.addWidget(self.aircraft_Mach_plot)
    plot_layout.addWidget(self.aircraft_CAS_plot) 
    
    return 
