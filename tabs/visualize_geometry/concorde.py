import RCAIDE
from RCAIDE.Framework.Core import Units , Data        
from RCAIDE.Library.Methods.Propulsors.Turbofan_Propulsor                      import design_turbofan
from RCAIDE.Library.Methods.Stability.Center_of_Gravity                        import compute_component_centers_of_gravity 
from RCAIDE.Library.Plots.Geometry.plot_3d_fuselage                            import generate_3d_fuselage_points   
from RCAIDE.Library.Methods.Propulsors.Turbojet_Propulsor                      import design_turbojet   
from RCAIDE.Framework.Networks.Electric                                        import Electric 
from RCAIDE.Library.Methods.Geometry.Planform                                  import segment_properties,wing_segmented_planform    
from RCAIDE.Library.Methods.Energy.Sources.Batteries.Common                    import initialize_from_circuit_configuration 
from RCAIDE.Library.Methods.Weights.Correlation_Buildups.Propulsion            import nasa_motor
from RCAIDE.Library.Methods.Propulsors.Converters.DC_Motor                     import design_motor
from RCAIDE.Library.Methods.Propulsors.Converters.Rotor                        import design_propeller ,design_lift_rotor 
from RCAIDE.Library.Methods.Weights.Physics_Based_Buildups.Electric            import compute_weight , converge_weight 
from RCAIDE.Library.Plots                                                      import *       
from RCAIDE.Library.Plots                                                      import *  
from RCAIDE.Library.Plots     import *     

# python imports 
import numpy as np  
from copy import deepcopy
import os

# python imports 
import numpy as np  
from copy import deepcopy 
import os
import sys
import vtk
from PyQt6 import QtCore, QtGui
from PyQt6 import QtWidgets, QtCore, QtGui
# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import (
    vtkFloatArray,
    vtkIdList,
    vtkPoints
)
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
    vtkPolyData
)
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCamera,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

def show_vtk():
    # Create a renderer, render window, and interactor
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    # Set up the Concorde vehicle (assuming Concorde_vehicle_setup is defined elsewhere)
    vehicle = Concorde_vehicle_setup()

    # Number of points for airfoil
    number_of_airfoil_points = 21

    # Plot wings
    for wing in vehicle.wings:  
        n_segments = len(wing.Segments)  
        dim = n_segments if n_segments > 0 else 2
        GEOM = generate_3d_wing_points(wing, number_of_airfoil_points, dim)
        actor = generate_vtk_object(GEOM.PTS)
        renderer.AddActor(actor)

        if wing.symmetric:
            if wing.vertical: 
                GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
            else:
                GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
            actor = generate_vtk_object(GEOM.PTS)
            renderer.AddActor(actor)

    # Plot fuselage
    for fuselage in vehicle.fuselages:
        GEOM = generate_3d_fuselage_points(fuselage, tessellation=24)
        actor = generate_vtk_object(GEOM.PTS)
        renderer.AddActor(actor)

    # Plot booms
    for boom in vehicle.booms:
        GEOM = generate_3d_fuselage_points(boom, tessellation=24)
        actor = generate_vtk_object(GEOM.PTS)
        renderer.AddActor(actor)

    # Plot rotors and propellers
    number_of_airfoil_points = 11
    for network in vehicle.networks:
        for bus in network.busses:
            for propulsor in bus.propulsors:
                # Nacelle handling
                if 'nacelle' in propulsor:
                    nacelle = propulsor.nacelle
                    if isinstance(nacelle, RCAIDE.Library.Components.Nacelles.Stack_Nacelle):
                        GEOM = generate_3d_stack_nacelle_points(nacelle, tessellation=24, number_of_airfoil_points=21)
                    elif isinstance(nacelle, RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle):
                        GEOM = generate_3d_BOR_nacelle_points(nacelle, tessellation=24, number_of_airfoil_points=21)
                    else:
                        GEOM = generate_3d_basic_nacelle_points(nacelle, tessellation=24, number_of_airfoil_points=21)
                    actor = generate_vtk_object(GEOM.PTS)
                    renderer.AddActor(actor)

                # Rotor handling
                if 'rotor' in propulsor:
                    num_B = propulsor.rotor.number_of_blades
                    dim = len(propulsor.rotor.radius_distribution)
                    for i in range(num_B):
                        GEOM = generate_3d_blade_points(propulsor.rotor, number_of_airfoil_points, dim, i)
                        actor = generate_vtk_object(GEOM.PTS[0])
                        renderer.AddActor(actor)

                # Propeller handling
                if 'propeller' in propulsor:
                    num_B = propulsor.propeller.number_of_blades
                    dim = len(propulsor.propeller.radius_distribution)
                    for i in range(num_B):
                        GEOM = generate_3d_blade_points(propulsor.propeller, number_of_airfoil_points, dim, i)
                        actor = generate_vtk_object(GEOM.PTS[0])
                        renderer.AddActor(actor)

    # Set camera and render settings
    camera = vtk.vtkCamera()
    camera.SetPosition(1, 1, 1)
    camera.SetFocalPoint(0, 0, 0)

    renderer.SetActiveCamera(camera)
    renderer.ResetCamera()
    renderer.SetBackground(0.1, 0.2, 0.4)  # Background color
    renderer.SetViewport(0, 0, 1, 1)

    # Render and start interaction
    render_window.Render()
    render_window_interactor.Start()


# Utility functions to generate the VTK objects (same as from your code)
def generate_vtk_object(pts):
    comp = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    polys = vtk.vtkCellArray()
    scalars = vtk.vtkFloatArray()

    size = np.shape(pts)
    n_r = size[0]
    n_a = size[1]
    n = n_a * (n_r - 1)  # total number of cells
    X = pts.reshape(n_r * n_a, 3)
    geom_pts = write_azimuthal_cell_values(X, n, n_a)

    size = np.shape(X)
    for i, fxi in enumerate(X):
        points.InsertPoint(i, fxi)
        scalars.InsertTuple1(i, i)
    for pt in geom_pts:
        polys.InsertNextCell(mkVtkIdList(pt))

    comp.SetPoints(points)
    comp.SetPolys(polys)
    comp.GetPointData().SetScalars(scalars)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(comp)
    mapper.SetScalarRange(comp.GetScalarRange())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    return actor


def mkVtkIdList(it):
    vil = vtk.vtkIdList()
    for i in it:
        vil.InsertNextId(int(i))
    return vil


def write_azimuthal_cell_values(f, n_cells, n_a):
    rlap = 0
    adjacent_cells = np.zeros((n_cells, 4))

    for i in range(n_cells):
        if i == (n_a - 1 + n_a * rlap):
            b = i - (n_a - 1)
            c = i + 1
            rlap += 1
        else:
            b = i + 1
            c = i + n_a + 1
        a = i
        d = i + n_a
        adjacent_cells[i, 0] = a
        adjacent_cells[i, 1] = b
        adjacent_cells[i, 2] = c
        adjacent_cells[i, 3] = d
    return adjacent_cells

def Concorde_vehicle_setup():
    # ------------------------------------------------------------------
    #   Initialize the Vehicle
    # ------------------------------------------------------------------    
    
    vehicle = RCAIDE.Vehicle()
    vehicle.tag = 'Concorde'    
    
    
    # ------------------------------------------------------------------
    #   Vehicle-level Properties
    # ------------------------------------------------------------------    

    # mass properties
    vehicle.mass_properties.max_takeoff               = 185000.   # kg
    vehicle.mass_properties.operating_empty           = 78700.   # kg
    vehicle.mass_properties.takeoff                   = 183000.   # kg, adjusted due to significant fuel burn on runway
    vehicle.mass_properties.cargo                     = 1000.  * Units.kilogram   
    vehicle.mass_properties.max_zero_fuel             = 92000.
        
    # envelope properties
    #vehicle.flight_envelope.ultimate_load = 3.75
    #vehicle.flight_envelope.limit_load    = 2.5

    # basic parameters
    vehicle.reference_area               = 358.25      
    vehicle.passengers                   = 100
    vehicle.systems.control              = "fully powered" 
    vehicle.systems.accessories          = "sst"
    vehicle.maximum_cross_sectional_area = 13.9
    vehicle.total_length                 = 61.66
    vehicle.design_mach_number           = 2.02
    vehicle.design_range                 = 4505 * Units.miles
    vehicle.design_cruise_alt            = 60000.0 * Units.ft
    
    # ------------------------------------------------------------------        
    #   Main Wing
    # ------------------------------------------------------------------        
    
    wing = RCAIDE.Library.Components.Wings.Main_Wing()
    wing.tag = 'main_wing'
    
    wing.aspect_ratio            = 1.83
    wing.sweeps.quarter_chord    = 59.5 * Units.deg
    wing.sweeps.leading_edge     = 66.5 * Units.deg
    wing.thickness_to_chord      = 0.03
    wing.taper                   = 0.
    
    wing.spans.projected           = 25.6    
    
    wing.chords.root               = 33.8
    wing.total_length              = 33.8
    wing.chords.tip                = 1.1
    wing.chords.mean_aerodynamic   = 18.4
    
    wing.areas.reference           = 358.25 
    wing.areas.wetted              = 601.
    wing.areas.exposed             = 326.5
    wing.areas.affected            = .6*wing.areas.reference
    
    wing.twists.root               = 0.0 * Units.degrees
    wing.twists.tip                = 0.0 * Units.degrees
    
    wing.origin                    = [[14,0,-.8]]
    wing.aerodynamic_center        = [35,0,0] 
    
    wing.vertical                  = False
    wing.symmetric                 = True
    wing.high_lift                 = True
    wing.vortex_lift               = True
    wing.high_mach                 = True 
    wing.dynamic_pressure_ratio    = 1.0
     
    wing_airfoil                   = RCAIDE.Library.Components.Airfoils.Airfoil()  
    ospath                         = os.path.abspath(__file__)
    separator                      = os.path.sep
    rel_path                       = os.path.dirname(ospath) + separator   + '..'  + separator  

    
    # Base directory where this file is located
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct path to airfoil
    airfoil_dir = os.path.join(base_dir, 'Airfoils')
    naca65_203_path = os.path.join(airfoil_dir, 'NACA65_203.txt')

    # Wing airfoil setup
    wing_airfoil = RCAIDE.Library.Components.Airfoils.Airfoil()
    wing_airfoil.coordinate_file = naca65_203_path  # Use relative path
    wing.append_airfoil(wing_airfoil)
    
    
    # set root sweep with inner section
    segment = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                   = 'section_1'
    segment.percent_span_location = 0.
    segment.twist                 = 0. * Units.deg
    segment.root_chord_percent    = 1
    segment.dihedral_outboard     = 0.
    segment.sweeps.quarter_chord  = 67. * Units.deg
    segment.thickness_to_chord    = 0.03
    segment.append_airfoil(wing_airfoil)
    wing.Segments.append(segment)
    
    # set section 2 start point
    segment = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                   = 'section_2'
    segment.percent_span_location = (6.15 * 2) /wing.spans.projected
    segment.twist                 = 0. * Units.deg
    segment.root_chord_percent    = 13.8/wing.chords.root
    segment.dihedral_outboard     = 0.
    segment.sweeps.quarter_chord  = 48. * Units.deg
    segment.thickness_to_chord    = 0.03
    segment.append_airfoil(wing_airfoil)
    wing.Segments.append(segment)
    
    
    # set section 3 start point
    segment = RCAIDE.Library.Components.Wings.Segment() 
    segment.tag                   = 'section_3'
    segment.percent_span_location = (12.1 *2) /wing.spans.projected
    segment.twist                 = 0. * Units.deg
    segment.root_chord_percent    = 4.4/wing.chords.root
    segment.dihedral_outboard     = 0.
    segment.sweeps.quarter_chord  = 71. * Units.deg 
    segment.thickness_to_chord    = 0.03
    segment.append_airfoil(wing_airfoil)
    wing.Segments.append(segment)  
    
    # set tip
    segment = RCAIDE.Library.Components.Wings.Segment() 
    segment.tag                   = 'tip'
    segment.percent_span_location = 1.
    segment.twist                 = 0. * Units.deg
    segment.root_chord_percent    = 1.1/wing.chords.root
    segment.dihedral_outboard     = 0.
    segment.sweeps.quarter_chord  = 0.
    segment.thickness_to_chord    = 0.03
    segment.append_airfoil(wing_airfoil)
    wing.Segments.append(segment)      
    
    # Fill out more segment properties automatically
    wing = wing_segmented_planform(wing)        
    
    
    # add to vehicle
    vehicle.append_component(wing)
    
    
    # ------------------------------------------------------------------
    #   Vertical Stabilizer
    # ------------------------------------------------------------------
    
    wing = RCAIDE.Library.Components.Wings.Vertical_Tail()
    wing.tag = 'vertical_stabilizer'    
    
    wing.aspect_ratio            = 0.74     
    wing.sweeps.quarter_chord    = 60 * Units.deg
    wing.thickness_to_chord      = 0.04
    wing.taper                   = 0.14 
    wing.spans.projected         = 6.0     
    wing.chords.root             = 14.5
    wing.total_length            = 14.5
    wing.chords.tip              = 2.7
    wing.chords.mean_aerodynamic = 8.66 
    wing.areas.reference         = 33.91     
    wing.areas.wetted            = 76. 
    wing.areas.exposed           = 38.
    wing.areas.affected          = 33.91 
    wing.twists.root             = 0.0 * Units.degrees
    wing.twists.tip              = 0.0 * Units.degrees   
    wing.origin                  = [[42.,0,1.]]
    wing.aerodynamic_center      = [50,0,0]     
    wing.vertical                = True 
    wing.symmetric               = False
    wing.t_tail                  = False
    wing.high_mach               = True     
    
    wing.dynamic_pressure_ratio  = 1.0
    
    


    supersonic_tail_path = os.path.join(airfoil_dir, 'supersonic_tail.txt')
    
    tail_airfoil = RCAIDE.Library.Components.Airfoils.Airfoil() 
    tail_airfoil.coordinate_file = supersonic_tail_path
    
    wing.append_airfoil(tail_airfoil)  
    
    

    
    
        

    # set root sweep with inner section
    segment = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                   = 'section_1'
    segment.percent_span_location = 0.0
    segment.twist                 = 0. * Units.deg
    segment.root_chord_percent    = 14.5/14.5
    segment.dihedral_outboard     = 0.
    segment.sweeps.quarter_chord  = 63. * Units.deg
    segment.thickness_to_chord    = 0.04
    segment.append_airfoil(tail_airfoil)
    wing.Segments.append(segment)
    
    # set mid section start point
    segment = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                   = 'section_2'
    segment.percent_span_location = 2.4/(6.0) + wing.Segments['section_1'].percent_span_location
    segment.twist                 = 0. * Units.deg
    segment.root_chord_percent    = 7.5/14.5
    segment.dihedral_outboard     = 0.
    segment.sweeps.quarter_chord  = 40. * Units.deg
    segment.thickness_to_chord    = 0.04
    segment.append_airfoil(tail_airfoil)
    wing.Segments.append(segment)
    
    # set tip
    segment = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                   = 'tip'
    segment.percent_span_location = 1.
    segment.twist                 = 0. * Units.deg
    segment.root_chord_percent    = 2.7/14.5
    segment.dihedral_outboard     = 0.
    segment.sweeps.quarter_chord  = 0.
    segment.thickness_to_chord    = 0.04
    segment.append_airfoil(tail_airfoil)
    wing.Segments.append(segment)    
    
    # Fill out more segment properties automatically
    wing = wing_segmented_planform(wing)        
    
    # add to vehicle
    vehicle.append_component(wing)    


    # ------------------------------------------------------------------
    #  Fuselage
    # ------------------------------------------------------------------
    
    fuselage                                        = RCAIDE.Library.Components.Fuselages.Tube_Fuselage() 
    fuselage.seats_abreast                          = 4
    fuselage.seat_pitch                             = 38. * Units.inches 
    fuselage.fineness.nose                          = 4.3
    fuselage.fineness.tail                          = 6.4 
    fuselage.lengths.total                          = 61.66   
    fuselage.width                                  = 2.88 
    fuselage.heights.maximum                        = 3.32    
    fuselage.heights.maximum                        = 3.32    
    fuselage.heights.at_quarter_length              = 3.32    
    fuselage.heights.at_wing_root_quarter_chord     = 3.32    
    fuselage.heights.at_three_quarters_length       = 3.32    
    fuselage.areas.wetted                           = 442.
    fuselage.areas.front_projected                  = 11.9 
    fuselage.effective_diameter                     = 3.1 
    fuselage.differential_pressure                  = 7.4e4 * Units.pascal    # Maximum differential pressure 
    
    fuselage.OpenVSP_values = Data() # VSP uses degrees directly
    
    fuselage.OpenVSP_values.nose = Data()
    fuselage.OpenVSP_values.nose.top = Data()
    fuselage.OpenVSP_values.nose.side = Data()
    fuselage.OpenVSP_values.nose.top.angle = 20.0
    fuselage.OpenVSP_values.nose.top.strength = 0.75
    fuselage.OpenVSP_values.nose.side.angle = 20.0
    fuselage.OpenVSP_values.nose.side.strength = 0.75  
    fuselage.OpenVSP_values.nose.TB_Sym = True
    fuselage.OpenVSP_values.nose.z_pos = -.01
    
    fuselage.OpenVSP_values.tail = Data()
    fuselage.OpenVSP_values.tail.top = Data()
    fuselage.OpenVSP_values.tail.side = Data()    
    fuselage.OpenVSP_values.tail.bottom = Data()
    fuselage.OpenVSP_values.tail.top.angle = 0.0
    fuselage.OpenVSP_values.tail.top.strength = 0.0 
    
    
    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_0'    
    segment.percent_x_location                  = 0.0000
    segment.percent_z_location                  =  -0.61 /fuselage.lengths.total 
    segment.height                              = 0.00100 
    segment.width                               = 0.00100  
    fuselage.Segments.append(segment)   
     
    
    # Segment                                   
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment()
    segment.tag                                 = 'segment_1'   
    segment.percent_x_location                  = 3.02870/fuselage.lengths.total   
    segment.percent_z_location                  = -0.3583/fuselage.lengths.total     
    segment.height                              = 1.4502  
    segment.width                               = 1.567  
    fuselage.Segments.append(segment)
    

    
    # Segment                                   
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment()
    segment.tag                                 = 'segment_2'   
    segment.percent_x_location                  =   5.7742/fuselage.lengths.total   
    segment.percent_z_location                  =  -0.1500/fuselage.lengths.total    
    segment.height                              = 2.356  
    segment.width                               = 2.3429  
    fuselage.Segments.append(segment)
    

    # Segment                                   
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment()
    segment.tag                                 = 'segment_3'   
    segment.percent_x_location                  =  9.0791/fuselage.lengths.total    
    segment.percent_z_location                  = 0  
    segment.height                              = 3.0581  
    segment.width                               = 2.741  
    fuselage.Segments.append(segment)
     
    
    
    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_4'    
    segment.percent_x_location                  = 12.384/fuselage.lengths.total  
    segment.percent_z_location                  = 0  
    segment.height                              = 3.3200 
    segment.width                               = 2.880  
    fuselage.Segments.append(segment)
    
    # Segment                                   
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment()
    segment.tag                                 = 'segment_6'   
    segment.percent_x_location                  = 43.228 /fuselage.lengths.total    
    segment.percent_z_location                  = 0 
    segment.height                              = 3.3200   
    segment.width                               = 2.8800  
    fuselage.Segments.append(segment)

    # Segment                                   
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment()
    segment.tag                                 = 'segment_6'   
    segment.percent_x_location                  =  47.5354/fuselage.lengths.total     
    segment.percent_z_location                  =  0.100/fuselage.lengths.total     
    segment.height                              = 2.952  
    segment.width                               = 2.8800  
    fuselage.Segments.append(segment)   

                 
    # Segment                                   
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment()
    segment.tag                                 = 'segment_7'   
    segment.percent_x_location                  = 1  
    segment.percent_z_location                  = 1.2332/fuselage.lengths.total   
    segment.height                              = 0.00100  
    segment.width                               = 0.00100  
    fuselage.Segments.append(segment)
    
    
    vehicle.append_component(fuselage)

    #------------------------------------------------------------------------------------------------------------------------------------  
    #  Turbojet Network
    #------------------------------------------------------------------------------------------------------------------------------------  
    net                                            = RCAIDE.Framework.Networks.Fuel() 
    
    #------------------------------------------------------------------------------------------------------------------------------------  
    # Fuel Distrubition Line 
    #------------------------------------------------------------------------------------------------------------------------------------  
    fuel_line                                     = RCAIDE.Library.Components.Energy.Distributors.Fuel_Line() 
    fuel_line.identical_propulsors                = False # for regression 
    

    #------------------------------------------------------------------------------------------------------------------------------------  
    #  Inner Right Propulsor
    #------------------------------------------------------------------------------------------------------------------------------------   
    outer_right_turbojet                          = RCAIDE.Library.Components.Propulsors.Turbojet()  
    outer_right_turbojet.tag                      = 'outer_right_turbojet'   
    outer_right_turbojet.active_fuel_tanks        = ['tank_6_and_7','tank_5A_and_7A','tank_2_and_3','tank_11']    
    outer_right_turbojet.engine_length            = 4.039
    outer_right_turbojet.nacelle_diameter         = 1.3
    outer_right_turbojet.inlet_diameter           = 1.212 
    outer_right_turbojet.areas.wetted             = 30
    outer_right_turbojet.design_altitude          = 60000.0*Units.ft
    outer_right_turbojet.design_mach_number       = 2.02
    outer_right_turbojet.design_thrust            = 10000. * Units.lbf  
    outer_right_turbojet.origin                   = [[37.,5.5,-1.6]] 
    outer_right_turbojet.working_fluid            = RCAIDE.Library.Attributes.Gases.Air()
    
    # Ram  
    ram                                           = RCAIDE.Library.Components.Propulsors.Converters.Ram()
    ram.tag                                       = 'ram' 
    outer_right_turbojet.ram                      = ram 
         
    # Inlet Nozzle         
    inlet_nozzle                                  = RCAIDE.Library.Components.Propulsors.Converters.Compression_Nozzle()
    inlet_nozzle.tag                              = 'inlet_nozzle' 
    inlet_nozzle.polytropic_efficiency            = 1.0
    inlet_nozzle.pressure_ratio                   = 1.0
    inlet_nozzle.pressure_recovery                = 0.94 
    outer_right_turbojet.inlet_nozzle             = inlet_nozzle    
          
    #  Low Pressure Compressor      
    lp_compressor                                 = RCAIDE.Library.Components.Propulsors.Converters.Compressor()    
    lp_compressor.tag                             = 'low_pressure_compressor' 
    lp_compressor.polytropic_efficiency           = 0.88
    lp_compressor.pressure_ratio                  = 3.1     
    outer_right_turbojet.low_pressure_compressor  = lp_compressor         
        
    # High Pressure Compressor        
    hp_compressor                                 = RCAIDE.Library.Components.Propulsors.Converters.Compressor()    
    hp_compressor.tag                             = 'high_pressure_compressor' 
    hp_compressor.polytropic_efficiency           = 0.88
    hp_compressor.pressure_ratio                  = 5.0  
    outer_right_turbojet.high_pressure_compressor = hp_compressor
 
    # Low Pressure Turbine 
    lp_turbine                                    = RCAIDE.Library.Components.Propulsors.Converters.Turbine()   
    lp_turbine.tag                                ='low_pressure_turbine' 
    lp_turbine.mechanical_efficiency              = 0.99
    lp_turbine.polytropic_efficiency              = 0.89 
    outer_right_turbojet.low_pressure_turbine     = lp_turbine      
             
    # High Pressure Turbine         
    hp_turbine                                    = RCAIDE.Library.Components.Propulsors.Converters.Turbine()   
    hp_turbine.tag                                ='high_pressure_turbine' 
    hp_turbine.mechanical_efficiency              = 0.99
    hp_turbine.polytropic_efficiency              = 0.87 
    outer_right_turbojet.high_pressure_turbine    = hp_turbine   
          
    # Combustor   
    combustor                                     = RCAIDE.Library.Components.Propulsors.Converters.Combustor()   
    combustor.tag                                 = 'combustor' 
    combustor.efficiency                          = 0.94
    combustor.alphac                              = 1.0     
    combustor.turbine_inlet_temperature           = 1440.
    combustor.pressure_ratio                      = 0.92
    combustor.fuel_data                           = RCAIDE.Library.Attributes.Propellants.Jet_A()     
    outer_right_turbojet.combustor                = combustor
     
    #  Afterburner  
    afterburner                                   = RCAIDE.Library.Components.Propulsors.Converters.Combustor()   
    afterburner.tag                               = 'afterburner' 
    afterburner.efficiency                        = 0.9
    afterburner.alphac                            = 1.0     
    afterburner.turbine_inlet_temperature         = 1500
    afterburner.pressure_ratio                    = 1.0
    afterburner.fuel_data                         = RCAIDE.Library.Attributes.Propellants.Jet_A()     
    outer_right_turbojet.afterburner              = afterburner   
 
    # Core Nozzle 
    nozzle                                        = RCAIDE.Library.Components.Propulsors.Converters.Supersonic_Nozzle()   
    nozzle.tag                                    = 'core_nozzle' 
    nozzle.pressure_recovery                      = 0.95
    nozzle.pressure_ratio                         = 1.    
    outer_right_turbojet.core_nozzle              = nozzle
    
    # design turbojet 
    design_turbojet(outer_right_turbojet) 

    nacelle                                     = RCAIDE.Library.Components.Nacelles.Stack_Nacelle()
    nacelle.diameter                            = 1.3
    nacelle.tag                                 = 'nacelle_1'
    nacelle.origin                              = [[37.,5.5,-1.6]] 
    nacelle.length                              = 10
    nacelle.inlet_diameter                      = 1.1 
    nacelle.areas.wetted                        = 30.
    
    nac_segment                                 = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                             = 'segment_1' 
    nac_segment.orientation_euler_angles        = [0., -45*Units.degrees,0.]     
    nac_segment.percent_x_location              = 0.0  
    nac_segment.height                          = 2.12
    nac_segment.width                           = 1.5
    nac_segment.curvature                       = 5
    nacelle.append_segment(nac_segment)         

    nac_segment                                 = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                             = 'segment_2'
    nac_segment.percent_x_location              = 1.0
    nac_segment.height                          = 1.5
    nac_segment.width                           = 1.5
    nac_segment.curvature                       = 5
    nacelle.append_segment(nac_segment)      
    outer_right_turbojet.nacelle = nacelle  
    fuel_line.propulsors.append(outer_right_turbojet) 

    #------------------------------------------------------------------------------------------------------------------------------------  
    #  Inner Right Propulsor
    #------------------------------------------------------------------------------------------------------------------------------------   
    inner_right_turbojet                     = deepcopy(outer_right_turbojet) 
    inner_right_turbojet.tag                 = 'inner_right_turbojet'      
    inner_right_turbojet.origin              = [[37.,4,-1.6]]   
    inner_right_turbojet.active_fuel_tanks   = ['tank_6_and_7','tank_5A_and_7A','tank_2_and_3','tank_11']  
    nacelle_2                                = deepcopy(nacelle)
    nacelle_2.tag                            = 'nacelle_2'
    nacelle_2.origin                         = [[37.,4,-1.6]]
    inner_right_turbojet.nacelle = nacelle_2 
    fuel_line.propulsors.append(inner_right_turbojet) 

    #------------------------------------------------------------------------------------------------------------------------------------  
    #  Inner Right Propulsor
    #------------------------------------------------------------------------------------------------------------------------------------    
    inner_left_turbojet                     = deepcopy(outer_right_turbojet)    
    inner_left_turbojet.tag                 = 'inner_left_turbojet'  
    inner_left_turbojet.origin              = [[37.,-4,-1.6]]  
    inner_left_turbojet.active_fuel_tanks   = ['tank_9','tank_10','tank_1_and_4','tank_5_and_8'] 
    nacelle_3                               = deepcopy(nacelle)
    nacelle_3.tag                           = 'nacelle_3'
    nacelle_3.origin                        = [[37.,-4,-1.6]]
    inner_left_turbojet.nacelle = nacelle_3 
    fuel_line.propulsors.append(inner_left_turbojet) 

    #------------------------------------------------------------------------------------------------------------------------------------  
    #  Inner Left Propulsor
    #------------------------------------------------------------------------------------------------------------------------------------    
    outer_left_turbojet                     = deepcopy(outer_right_turbojet)
    outer_left_turbojet.tag                 = 'outer_left_turbojet'     
    outer_left_turbojet.active_fuel_tanks   = ['tank_9','tank_10','tank_1_and_4','tank_5_and_8']   
    outer_left_turbojet.origin              = [[37.,-5.5,-1.6]]   
    nacelle_4                               = deepcopy(nacelle)
    nacelle_4.tag                           = 'nacelle_4'
    nacelle_4.origin                        = [[37.,-5.5,-1.6]]
    outer_left_turbojet.nacelle = nacelle_4
    fuel_line.propulsors.append(outer_left_turbojet) 

       
    #------------------------------------------------------------------------------------------------------------------------------------  
    #  Fuel Tank & Fuel
    #------------------------------------------------------------------------------------------------------------------------------------   
    fuel_tank                                      = RCAIDE.Library.Components.Energy.Sources.Fuel_Tanks.Fuel_Tank()
    fuel_tank.tag                                  = 'tank_9'
    fuel_tank.mass_properties.center_of_gravity    = np.array([[26.5,0,0]])
    fuel_tank.mass_properties.fuel_mass_when_full  = 11096
    fuel_tank.fuel_selector_ratio                  = 1/8
    fuel_tank.fuel                            = RCAIDE.Library.Attributes.Propellants.Jet_A() 
    fuel_line.fuel_tanks.append(fuel_tank) 
    
    fuel_tank                                      = RCAIDE.Library.Components.Energy.Sources.Fuel_Tanks.Fuel_Tank()
    fuel_tank.tag                                  = 'tank_10'
    fuel_tank.mass_properties.center_of_gravity    = np.array([[28.7,0,0]])
    fuel_tank.mass_properties.fuel_mass_when_full  = 11943
    fuel_tank.fuel_selector_ratio                  = 1/8
    fuel_tank.fuel                            = RCAIDE.Library.Attributes.Propellants.Jet_A() 
    fuel_line.fuel_tanks.append(fuel_tank) 
    
    fuel_tank                                      = RCAIDE.Library.Components.Energy.Sources.Fuel_Tanks.Fuel_Tank()
    fuel_tank.tag                                  = 'tank_1_and_4'
    fuel_tank.mass_properties.center_of_gravity    = np.array([[31.0,0,0]])
    fuel_tank.mass_properties.fuel_mass_when_full  = 4198+4198
    fuel_tank.fuel_selector_ratio                  = 1/8
    fuel_tank.fuel                            = RCAIDE.Library.Attributes.Propellants.Jet_A() 
    fuel_line.fuel_tanks.append(fuel_tank) 
    
    fuel_tank                                      = RCAIDE.Library.Components.Energy.Sources.Fuel_Tanks.Fuel_Tank()
    fuel_tank.tag                                  = 'tank_5_and_8'
    fuel_tank.mass_properties.center_of_gravity    = np.array([[32.9,0,0]])
    fuel_tank.mass_properties.fuel_mass_when_full  = 7200+12838
    fuel_tank.fuel_selector_ratio                  = 1/8
    fuel_tank.fuel                              = RCAIDE.Library.Attributes.Propellants.Jet_A() 
    fuel_line.fuel_tanks.append(fuel_tank) 
    
    fuel_tank                                      = RCAIDE.Library.Components.Energy.Sources.Fuel_Tanks.Fuel_Tank()
    fuel_tank.tag                                  = 'tank_6_and_7'
    fuel_tank.mass_properties.center_of_gravity    = np.array([[37.4,0,0]])
    fuel_tank.mass_properties.fuel_mass_when_full  = 11587+7405
    fuel_tank.fuel_selector_ratio                  = 1/8
    fuel_tank.fuel                                 = RCAIDE.Library.Attributes.Propellants.Jet_A() 
    fuel_line.fuel_tanks.append(fuel_tank) 
    
    fuel_tank                                      = RCAIDE.Library.Components.Energy.Sources.Fuel_Tanks.Fuel_Tank()
    fuel_tank.tag                                  = 'tank_5A_and_7A'
    fuel_tank.mass_properties.center_of_gravity    = np.array([[40.2,0,0]])
    fuel_tank.mass_properties.fuel_mass_when_full  = 2225+2225
    fuel_tank.fuel_selector_ratio                  = 1/8
    fuel_tank.fuel                                 = RCAIDE.Library.Attributes.Propellants.Jet_A() 
    fuel_line.fuel_tanks.append(fuel_tank) 
    
    fuel_tank                                      = RCAIDE.Library.Components.Energy.Sources.Fuel_Tanks.Fuel_Tank()
    fuel_tank.tag                                  = 'tank_2_and_3'
    fuel_tank.mass_properties.center_of_gravity    = np.array([[40.2,0,0]])
    fuel_tank.mass_properties.fuel_mass_when_full  = 4570+4570
    fuel_tank.fuel_selector_ratio                  = 1/8
    fuel_tank.fuel                                 = RCAIDE.Library.Attributes.Propellants.Jet_A() 
    fuel_line.fuel_tanks.append(fuel_tank)  
 
    fuel_tank = RCAIDE.Library.Components.Energy.Sources.Fuel_Tanks.Fuel_Tank()
    fuel_tank.tag                                  = 'tank_11'
    fuel_tank.mass_properties.center_of_gravity    = np.array([[49.8,0,0]])
    fuel_tank.mass_properties.fuel_mass_when_full  = 10415
    fuel_tank.fuel_selector_ratio                  = 1/8
    fuel_tank.fuel                            = RCAIDE.Library.Attributes.Propellants.Jet_A() 
    fuel_line.fuel_tanks.append(fuel_tank)      
    
     # Append fuel line to network      
    net.fuel_lines.append(fuel_line)    
  
    #------------------------------------------------------------------------------------------------------------------------------------          
    # Append energy network to aircraft 
    vehicle.append_energy_network(net)       

    return vehicle
