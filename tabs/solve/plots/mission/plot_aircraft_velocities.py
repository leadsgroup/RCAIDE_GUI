# RCAIDE_GUI/tabs/solve/plots/plot_aircraft_velocities.py
# 
# 
# Created:  Jul 2023, M. Clarke

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ----------------------------------------------------------------------------------------------------------------------  
from RCAIDE.Framework.Core import Units   
import numpy as np 
import pyqtgraph as pg

# ----------------------------------------------------------------------------------------------------------------------
#  PLOTS
# ----------------------------------------------------------------------------------------------------------------------   
def plot_aircraft_velocities(self,
                             results, 
                             plot_parameters,  
                             save_filename = "Aircraft Velocities",
                             file_type = ".png"):
    """
    Creates a multi-panel visualization of aircraft velocity components over a mission.

    Parameters
    ----------
    results : Results
        RCAIDE results data structure containing segment conditions
        
    save_figure : bool, optional
        Flag for saving the figure (default: False)
        
    show_legend : bool, optional
        Flag to display segment legend (default: True)
        
    save_filename : str, optional
        Name of file for saved figure (default: "Aircraft Velocities")
        
    file_type : str, optional
        File extension for saved figure (default: ".png")
        
    width : float, optional
        Figure width in inches (default: 11)
        
    height : float, optional
        Figure height in inches (default: 7)

    Returns
    -------
    fig : matplotlib.figure.Figure
        Handle to the generated figure containing four subplots:
            - True airspeed
            - Equivalent airspeed
            - Calibrated airspeed
            - Mach number

    Notes
    -----
    Creates a four-panel plot showing:
        1. True airspeed vs time
        2. Equivalent airspeed vs time
        3. Calibrated airspeed vs time
        4. Mach number vs time
    
    **Major Assumptions**
    
    * Results contain freestream conditions
    * Time is in minutes
    * Velocities are in knots
    * Standard atmosphere density used as reference

    **Definitions**
    
    'True Airspeed'
        Actual aircraft velocity relative to airmass
    'Equivalent Airspeed'
        Velocity at sea level producing same dynamic pressure
    'Calibrated Airspeed'
        Indicated airspeed corrected for instrument and position errors
    'Mach Number'
        Ratio of true airspeed to local speed of sound
    
    See Also
    --------
    RCAIDE.Library.Plots.Mission.plot_flight_conditions : Related atmospheric conditions
    RCAIDE.Library.Plots.Mission.plot_flight_trajectory : Complete trajectory visualization
    """

    max_velocity = 0
    max_EAS      = 0
    max_mach     = 0
    max_CAS      = 0
    for i, segment in enumerate(results.segments): 
        line_width    = plot_parameters.line_width
        rgba_color    = plot_parameters.line_colors[i]*255.0   
        segment_tag   = segment.tag.replace('_', ' ')
        marker        = plot_parameters.markers[0]
        marker_size   =  plot_parameters.marker_size 
        line_color    = (int(rgba_color[0]),int(rgba_color[1]),int(rgba_color[2]))
        line_style    = pg.mkPen(color=line_color, width=line_width)   #  pg.mkPen(color=(255, 0, 0), width=5)
        marker_color  = line_color
            
        time     = results.segments[i].conditions.frames.inertial.time[:,0] / Units.min
        velocity = results.segments[i].conditions.freestream.velocity[:,0] / Units.kts
        density  = results.segments[i].conditions.freestream.density[:,0]
        PR       = density/1.225
        EAS      = velocity * np.sqrt(PR)
        mach     = results.segments[i].conditions.freestream.mach_number[:,0]
        CAS      = EAS * (1+((1/8)*((1-PR)*mach**2))+((3/640)*(1-10*PR+(9*PR**2)*(mach**4)))) 
        
        max_velocity = np.maximum(np.max(velocity),max_velocity)
        max_EAS      = np.maximum(np.max(EAS),max_EAS)
        max_mach     = np.maximum(np.max(mach),max_mach)
        max_CAS      = np.maximum(np.max(CAS),max_CAS)
         
        # aircraft velocity plot 
        self.aircraft_TAS_plot.plot(time, velocity, pen=line_style,  symbol = marker ,  symbolSize=marker_size ,symbolBrush = marker_color,  name=segment_tag)
        self.aircraft_EAS_plot.plot(time, EAS, pen=line_style,  symbol = marker ,  symbolSize=marker_size ,symbolBrush = marker_color,  name=segment_tag)
        self.aircraft_Mach_plot.plot(time, mach, pen=line_style,  symbol = marker ,  symbolSize=marker_size ,symbolBrush = marker_color,  name=segment_tag)
        self.aircraft_CAS_plot.plot(time, CAS, pen=line_style,  symbol = marker ,  symbolSize=marker_size ,symbolBrush = marker_color,  name=segment_tag)
       
    self.aircraft_TAS_plot.setLabel("left", "True Airspeed (kts)", **plot_parameters.styles)
    self.aircraft_TAS_plot.setLabel("bottom", "Time (min)", **plot_parameters.styles)
    self.aircraft_TAS_plot.showGrid(x=plot_parameters.show_grid, y=plot_parameters.show_grid) 
    self.aircraft_TAS_plot.addLegend(labelTextSize=plot_parameters.legend_font_size)
    self.aircraft_TAS_plot.setYRange(0, max_velocity*1.2)

    self.aircraft_EAS_plot.setLabel("left", "Equiv. Airspeed (kts)", **plot_parameters.styles)
    self.aircraft_EAS_plot.setLabel("bottom", "Time (min)", **plot_parameters.styles)
    self.aircraft_EAS_plot.showGrid(x=plot_parameters.show_grid, y=plot_parameters.show_grid) 
    self.aircraft_EAS_plot.addLegend(labelTextSize=plot_parameters.legend_font_size)
    self.aircraft_EAS_plot.setYRange(0, max_EAS*1.2)
    

    self.aircraft_Mach_plot.setLabel("left", "Mach Number", **plot_parameters.styles)
    self.aircraft_Mach_plot.setLabel("bottom", "Time (min)", **plot_parameters.styles)
    self.aircraft_Mach_plot.showGrid(x=plot_parameters.show_grid, y=plot_parameters.show_grid) 
    self.aircraft_Mach_plot.addLegend(labelTextSize=plot_parameters.legend_font_size)
    self.aircraft_Mach_plot.setYRange(0, max_mach*1.2)
    

    self.aircraft_CAS_plot.setLabel("left", "Calibrated Airspeed (kts)", **plot_parameters.styles)
    self.aircraft_CAS_plot.setLabel("bottom", "Time (min)", **plot_parameters.styles)
    self.aircraft_CAS_plot.showGrid(x=plot_parameters.show_grid, y=plot_parameters.show_grid) 
    self.aircraft_CAS_plot.addLegend(labelTextSize=plot_parameters.legend_font_size)      
    self.aircraft_CAS_plot.setYRange(0, max_CAS*1.2)

  
    return  