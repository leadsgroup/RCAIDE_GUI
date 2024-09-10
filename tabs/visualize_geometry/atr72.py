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


def ATR_72_vehicle_setup():

    # ------------------------------------------------------------------
    #   Initialize the Vehicle
    # ------------------------------------------------------------------

    vehicle = RCAIDE.Vehicle()
    vehicle.tag = 'ATR_72'

    # ------------------------------------------------------------------
    #   Vehicle-level Properties
    # ------------------------------------------------------------------

    # mass properties
    vehicle.mass_properties.max_takeoff               = 23000 
    vehicle.mass_properties.takeoff                   = 23000  
    vehicle.mass_properties.operating_empty           = 13600  
    vehicle.mass_properties.max_zero_fuel             = 21000 
    vehicle.mass_properties.cargo                     = 7400
    vehicle.mass_properties.center_of_gravity         = [[0,0,0]] # Unknown 
    vehicle.mass_properties.moments_of_inertia.tensor = [[0,0,0]] # Unknown 
    vehicle.mass_properties.max_fuel                  = 5000
    vehicle.design_mach_number                        = 0.41 
    vehicle.design_range                              = 5471000 *Units.meter  
    vehicle.design_cruise_alt                         = 25000 *Units.feet

    # envelope properties
    vehicle.envelope.ultimate_load        = 3.75
    vehicle.envelope.limit_load           = 1.5
       
    # basic parameters       
    vehicle.reference_area                = 61.0  
    vehicle.passengers                    = 72
    vehicle.systems.control               = "fully powered"
    vehicle.systems.accessories           = "short range"  

 
    # ------------------------------------------------------------------
    #   Main Wing
    # ------------------------------------------------------------------

    wing                                  = RCAIDE.Library.Components.Wings.Main_Wing()
    wing.tag                              = 'main_wing'
    wing.areas.reference                  = 61.0  
    wing.spans.projected                  = 27.05 
    wing.aspect_ratio                     = (wing.spans.projected**2) /  wing.areas.reference
    wing.sweeps.quarter_chord             = 0.0 
    wing.thickness_to_chord               = 0.1 
    wing.chords.root                      = 2.7 
    wing.chords.tip                       = 1.35 
    wing.total_length                     = wing.chords.root  
    wing.taper                            = wing.chords.tip/wing.chords.root 
    wing.chords.mean_aerodynamic          = wing.chords.root * 2/3 * (( 1 + wing.taper + wing.taper**2 )/( 1 + wing.taper )) 
    wing.areas.exposed                    = 2 * wing.areas.reference
    wing.areas.wetted                     = 2 * wing.areas.reference 
    wing.twists.root                      = 0 * Units.degrees  
    wing.twists.tip                       = 0 * Units.degrees   
    wing.origin                           = [[11.52756129,0,2.009316366]]  
    wing.aerodynamic_center               = [[11.52756129 + 0.25*wing.chords.root ,0,2.009316366]]   
    wing.vertical                         = False   
    wing.symmetric                        = True  
    wing.dynamic_pressure_ratio           = 1.0 
 

    # Wing Segments 
    segment                               = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                           = 'inboard'
    segment.percent_span_location         = 0.0
    segment.twist                         = 0.0 * Units.deg
    segment.root_chord_percent            = 1. 
    segment.dihedral_outboard             = 0.0  * Units.degrees
    segment.sweeps.quarter_chord          = 0.0 * Units.degrees
    segment.thickness_to_chord            = .1 
    wing.append_segment(segment)
 
    segment                               = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                           = 'outboard'
    segment.percent_span_location         = 0.324
    segment.twist                         = 0.0 * Units.deg
    segment.root_chord_percent            = 1.0
    segment.dihedral_outboard             = 0.0 * Units.degrees
    segment.sweeps.leading_edge           = 4.7 * Units.degrees
    segment.thickness_to_chord            = .1 
    wing.append_segment(segment) 
 
    segment                               = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                           = 'tip'
    segment.percent_span_location         = 1.
    segment.twist                         = 0. * Units.degrees
    segment.root_chord_percent            = wing.taper 
    segment.thickness_to_chord            = 0.1
    segment.dihedral_outboard             = 0.
    segment.sweeps.quarter_chord          = 0.  
    wing.append_segment(segment)     
    
    # update properties of the wing using segments 
    wing = segment_properties(wing,update_wet_areas=True,update_ref_areas=True)
    
    # add to vehicle
    vehicle.append_component(wing)


    # ------------------------------------------------------------------
    #  Horizontal Stabilizer
    # ------------------------------------------------------------------ 
    wing                         = RCAIDE.Library.Components.Wings.Horizontal_Tail()
    wing.tag                     = 'horizontal_stabilizer'  
    wing.spans.projected         = 3.61*2 
    wing.areas.reference         = 15.2 
    wing.aspect_ratio            = (wing.spans.projected**2) /  wing.areas.reference
    wing.sweeps.leading_edge     = 11.56*Units.degrees  
    wing.thickness_to_chord      = 0.1  
    wing.chords.root             = 2.078645129 
    wing.chords.tip              = 0.953457347 
    wing.total_length            = wing.chords.root  
    wing.taper                   = wing.chords.tip/wing.chords.root  
    wing.chords.mean_aerodynamic = wing.chords.root * 2/3 * (( 1 + wing.taper + wing.taper**2 )/( 1 + wing.taper )) 
    wing.areas.exposed           = 2 * wing.areas.reference
    wing.areas.wetted            = 2 * wing.areas.reference 
    wing.twists.root             = 0 * Units.degrees  
    wing.twists.tip              = 0 * Units.degrees   
    wing.origin                  = [[25.505088,0,5.510942426]]   
    wing.aerodynamic_center      = [[25.505088+ 0.25*wing.chords.root,0,2.009316366]]   
    wing.vertical                = False  
    wing.symmetric               = True  
    wing.dynamic_pressure_ratio  = 1.0 

    # update properties of the wing using segments     
    wing = segment_properties(wing,update_wet_areas=True,update_ref_areas=True)

    # add to vehicle
    vehicle.append_component(wing)


    # ------------------------------------------------------------------
    #   Vertical Stabilizer
    # ------------------------------------------------------------------ 
    wing                                   = RCAIDE.Library.Components.Wings.Vertical_Tail()
    wing.tag                               = 'vertical_stabilizer'   
    wing.spans.projected                   = 4.5  
    wing.areas.reference                   = 12.7
    wing.sweeps.quarter_chord              = 54 * Units.degrees  
    wing.thickness_to_chord                = 0.1  
    wing.aspect_ratio                      = (wing.spans.projected**2) /  wing.areas.reference    
    wing.chords.root                       = 8.75
    wing.chords.tip                        = 1.738510759 
    wing.total_length                      = wing.chords.root  
    wing.taper                             = wing.chords.tip/wing.chords.root  
    wing.chords.mean_aerodynamic           = wing.chords.root * 2/3 * (( 1 + wing.taper + wing.taper**2 )/( 1 + wing.taper )) 
    wing.areas.exposed                     = 2 * wing.areas.reference
    wing.areas.wetted                      = 2 * wing.areas.reference 
    wing.twists.root                       = 0 * Units.degrees  
    wing.twists.tip                        = 0 * Units.degrees   
    wing.origin                            = [[17.34807199,0,1.3]]  
    wing.aerodynamic_center                = [[17.34807199,0,1.3]]   
    wing.vertical                          = True  
    wing.symmetric                         = False  
    wing.t_tail                            = True  
    wing.dynamic_pressure_ratio            = 1.0  
 

    # Wing Segments
    segment                               = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                           = 'segment_1'
    segment.percent_span_location         = 0.0
    segment.twist                         = 0.0
    segment.root_chord_percent            = 1.0
    segment.dihedral_outboard             = 0.0
    segment.sweeps.leading_edge           = 75 * Units.degrees  
    segment.thickness_to_chord            = 1.0
    wing.append_segment(segment)

    segment                               = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                           = 'segment_2'
    segment.percent_span_location         = 1.331360381/wing.spans.projected
    segment.twist                         = 0.0
    segment.root_chord_percent            = 4.25/wing.chords.root  
    segment.dihedral_outboard             = 0   
    segment.sweeps.leading_edge           = 54 * Units.degrees   
    segment.thickness_to_chord            = 0.1
    wing.append_segment(segment)

    segment                               = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                           = 'segment_3'
    segment.percent_span_location         = 3.058629978/wing.spans.projected
    segment.twist                         = 0.0
    segment.root_chord_percent            = 2.35/wing.chords.root    
    segment.dihedral_outboard             = 0 
    segment.sweeps.leading_edge           = 31 * Units.degrees   
    segment.thickness_to_chord            = 0.1
    wing.append_segment(segment)
    

    segment                               = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                           = 'segment_4'
    segment.percent_span_location         = 4.380739035/wing.spans.projected
    segment.twist                         = 0.0
    segment.root_chord_percent            = 2.190082795/wing.chords.root  
    segment.dihedral_outboard             = 0
    segment.sweeps.leading_edge           = 52 * Units.degrees   
    segment.thickness_to_chord            = 0.1
    wing.append_segment(segment)    
    

    segment                               = RCAIDE.Library.Components.Wings.Segment()
    segment.tag                           = 'segment_5'
    segment.percent_span_location         = 1.0
    segment.twist                         = 0.0
    segment.root_chord_percent            = 1.3/wing.chords.root  
    segment.dihedral_outboard             = 0  
    segment.sweeps.leading_edge           = 0 * Units.degrees   
    segment.thickness_to_chord            = 0.1
    wing.append_segment(segment)    

    # update properties of the wing using segments 
    wing = segment_properties(wing,update_wet_areas=True,update_ref_areas=True)
    
    # add to vehicle
    vehicle.append_component(wing)


    # ------------------------------------------------------------------
    #  Fuselage
    # ------------------------------------------------------------------

    fuselage = RCAIDE.Library.Components.Fuselages.Fuselage()
    fuselage.tag = 'fuselage' 
    fuselage.seats_abreast                      = 4 
    fuselage.seat_pitch                         = 18  
    fuselage.fineness.nose                      = 1.6
    fuselage.fineness.tail                      = 2. 
    fuselage.lengths.total                      = 27.12   
    fuselage.lengths.nose                       = 3.375147531 
    fuselage.lengths.tail                       = 9.2 
    fuselage.lengths.cabin                      = fuselage.lengths.total- (fuselage.lengths.nose + fuselage.lengths.tail  )
    fuselage.width                              = 2.985093814  
    fuselage.heights.maximum                    = 2.755708426  
    fuselage.areas.side_projected               = fuselage.heights.maximum * fuselage.lengths.total * Units['meters**2'] 
    fuselage.areas.wetted                       = np.pi * fuselage.width/2 * fuselage.lengths.total * Units['meters**2'] 
    fuselage.areas.front_projected              = np.pi * fuselage.width/2      * Units['meters**2']  
    fuselage.differential_pressure              = 5.0e4 * Units.pascal
    fuselage.heights.at_quarter_length          = fuselage.heights.maximum * Units.meter
    fuselage.heights.at_three_quarters_length   = fuselage.heights.maximum * Units.meter
    fuselage.heights.at_wing_root_quarter_chord = fuselage.heights.maximum* Units.meter
    
     # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_1'    
    segment.percent_x_location                  = 0.0000
    segment.percent_z_location                  = 0.0000
    segment.height                              = 1E-3
    segment.width                               = 1E-3  
    fuselage.Segments.append(segment)   
    
    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_2'    
    segment.percent_x_location                  = 0.08732056/fuselage.lengths.total  
    segment.percent_z_location                  = 0.0000
    segment.height                              = 0.459245202 
    segment.width                               = 0.401839552 
    fuselage.Segments.append(segment)   
  
    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_3'    
    segment.percent_x_location                  = 0.197094977/fuselage.lengths.total  
    segment.percent_z_location                  = 0.001
    segment.height                              = 0.688749197
    segment.width                               = 0.918490404  
    fuselage.Segments.append(segment)   

    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_4'    
    segment.percent_x_location                  = 0.41997031/fuselage.lengths.total 
    segment.percent_z_location                  = 0.0000 
    segment.height                              = 0.975896055   
    segment.width                               = 1.320329956 
    fuselage.Segments.append(segment)   

    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_5'    
    segment.percent_x_location                  = 0.753451685/fuselage.lengths.total
    segment.percent_z_location                  = 0.0014551442477876075 # this is given as a percentage of the fuselage length i.e. location of the center of the cross section/fuselage length
    segment.height                              = 1.320329956 
    segment.width                               = 1.664763858 
    fuselage.Segments.append(segment)   

    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_6'    
    segment.percent_x_location                  = 1.14389933/fuselage.lengths.total
    segment.percent_z_location                  = 0.0036330994100294946
    segment.height                              = 1.607358208   
    segment.width                               = 2.009316366 
    fuselage.Segments.append(segment)   

    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_7'    
    segment.percent_x_location                  = 1.585491874/fuselage.lengths.total
    segment.percent_z_location                  = 0.008262262758112099
    segment.height                              = 2.18141471 
    segment.width                               = 2.411155918 
    fuselage.Segments.append(segment)   

    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_8'    
    segment.percent_x_location                  = 2.031242539/fuselage.lengths.total
    segment.percent_z_location                  = 0.013612882669616513
    segment.height                              = 2.468442962  
    segment.width                               = 2.698065563  
    fuselage.Segments.append(segment)   

    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_9'    
    segment.percent_x_location                  = 2.59009412/fuselage.lengths.total
    segment.percent_z_location                  = 0.01636321766224188
    segment.height                              = 2.640659912   
    segment.width                               = 2.812876863 
    fuselage.Segments.append(segment)   

    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_10'    
    segment.percent_x_location                  = 3.375147531/fuselage.lengths.total
    segment.percent_z_location                  = 0.01860240047935103
    segment.height                              = 2.755708426
    segment.width                               = 2.985093814 
    fuselage.Segments.append(segment)   

    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_11'    
    segment.percent_x_location                  = 17.01420312/fuselage.lengths.total 
    segment.percent_z_location                  = 0.01860240047935103
    segment.height                              = 2.755708426
    segment.width                               = 2.985093814 
    fuselage.Segments.append(segment)   
 

    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_12'    
    segment.percent_x_location                  = 18.64210783/fuselage.lengths.total
    segment.percent_z_location                  = 0.01860240047935103
    segment.height                              = 2.698302776 
    segment.width                               = 2.927925377  
    fuselage.Segments.append(segment)    
     
     
    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_13'    
    segment.percent_x_location                  = 22.7416002/fuselage.lengths.total 
    segment.percent_z_location                  = 0.043363795685840714
    segment.height                              = 1.779575158  
    segment.width                               = 1.722050901 
    fuselage.Segments.append(segment)     
    
    # Segment  
    segment                                     = RCAIDE.Library.Components.Fuselages.Segment() 
    segment.tag                                 = 'segment_14'    
    segment.percent_x_location                  = 1.
    segment.percent_z_location                  = 0.06630560070058995
    segment.height                              = 0.401839552 
    segment.width                               = 0.401839552  
    fuselage.Segments.append(segment) 
    
    # add to vehicle
    vehicle.append_component(fuselage)  
    
    # ------------------------------------------------------------------
    #   Landing gear
    # ------------------------------------------------------------------  
    landing_gear                                = RCAIDE.Library.Components.Landing_Gear.Landing_Gear()
    main_gear                                   = RCAIDE.Library.Components.Landing_Gear.Main_Landing_Gear()
    nose_gear                                   = RCAIDE.Library.Components.Landing_Gear.Nose_Landing_Gear()
    main_gear.strut_length                      = 12. * Units.inches  
    nose_gear.strut_length                      = 6. * Units.inches 
                                                
    landing_gear.main                           = main_gear
    landing_gear.nose                           = nose_gear
                                                
    #add to vehicle                             
    vehicle.landing_gear                        = landing_gear

    # ########################################################  Energy Network  #########################################################  
    net                                         = RCAIDE.Framework.Networks.Fuel()   

    # add the network to the vehicle
    vehicle.append_energy_network(net) 

    #------------------------------------------------------------------------------------------------------------------------------------  
    # Bus
    #------------------------------------------------------------------------------------------------------------------------------------  
    fuel_line                                            = RCAIDE.Library.Components.Energy.Distributors.Fuel_Line()   

    #------------------------------------------------------------------------------------------------------------------------------------  
    #  Fuel Tank & Fuel
    #------------------------------------------------------------------------------------------------------------------------------------       
    fuel_tank                                            = RCAIDE.Library.Components.Energy.Sources.Fuel_Tanks.Fuel_Tank()
    fuel_tank.origin                                     = wing.origin  
    fuel                                                 = RCAIDE.Library.Attributes.Propellants.Aviation_Gasoline() 
    fuel.mass_properties.mass                            = 5000
    fuel.mass_properties.center_of_gravity               = wing.mass_properties.center_of_gravity
    fuel.internal_volume                                 = fuel.mass_properties.mass/fuel.density  
    fuel_tank.fuel                                       = fuel     
    fuel_line.fuel_tanks.append(fuel_tank)  

    #------------------------------------------------------------------------------------------------------------------------------------  
    # Propulsor
    #------------------------------------------------------------------------------------------------------------------------------------   
    starboard_propulsor                                  = RCAIDE.Library.Components.Propulsors.ICE_Propeller()     
    starboard_propulsor.active_fuel_tanks                = ['fuel_tank']   
                                                     
    # Engine                     
    starboard_engine                                     = RCAIDE.Library.Components.Propulsors.Converters.Engine()
    starboard_engine.sea_level_power                     = 2475 * Units.horsepower # 1,846 KW
    starboard_engine.flat_rate_altitude                  = 0.0
    starboard_engine.rated_speed                         = 1200* Units.rpm
    starboard_engine.power_specific_fuel_consumption     = 0.459 * Units['lb/hp/hr']
    starboard_engine.mass_properties.mass                = 480
    starboard_engine.lenght                              = 2.10
    starboard_engine.origin                              = [[ 9.559106394 ,-4.219315295, 1.616135105]]  
    starboard_propulsor.engine                           = starboard_engine 
     
    # Propeller 
    propeller = RCAIDE.Library.Components.Propulsors.Converters.Propeller()
    propeller.tag                                        = 'starboard_propeller'
    propeller.origin                                     = [[ 9.559106394 ,4.219315295, 1.616135105]]
    propeller.number_of_blades                           = 6.0
    propeller.tip_radius                                 = 3.93/2
    propeller.hub_radius                                 = 0.4
    propeller.cruise.design_freestream_velocity          = 280 * Units.knots
    propeller.cruise.design_angular_velocity             = 1200 * Units.rpm
    propeller.cruise.design_Cl                           = 0.7
    propeller.cruise.design_altitude                     = 25000  * Units.feet
    propeller.cruise.design_thrust                       = 10000 # incorrect 
    propeller.variable_pitch                             = True  
    ospath                                               = os.path.abspath(__file__)
    separator                                            = os.path.sep
    rel_path                                             = os.path.dirname(ospath) + separator + '..' + separator  
    airfoil                                              = RCAIDE.Library.Components.Airfoils.Airfoil()
    airfoil.tag                                          = 'NACA_4412' 
    
    
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct path to airfoil
    airfoil_dir = os.path.join(base_dir, 'Airfoils')
    polar_dir = os.path.join(base_dir, 'Airfoils', 'polars')
    
    atr72_path = os.path.join(airfoil_dir, 'NACA_4412.txt')
    
    
    
    airfoil.coordinate_file                              =  atr72_path   # absolute path   
    airfoil.polar_files                                  = [ os.path.join(polar_dir, 'NACA_4412_polar_Re_50000.txt'),
                                                            os.path.join(polar_dir, 'NACA_4412_polar_Re_100000.txt'),
                                                            os.path.join(polar_dir, 'NACA_4412_polar_Re_200000.txt'),
                                                            os.path.join(polar_dir, 'NACA_4412_polar_Re_500000.txt'),
                                                            os.path.join(polar_dir, 'NACA_4412_polar_Re_1000000.txt')]  
    propeller.append_airfoil(airfoil)                   
    propeller.airfoil_polar_stations                     = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]  
    propeller                                            = design_propeller(propeller)    
    starboard_propulsor.propeller                        = propeller 
    

    #------------------------------------------------------------------------------------------------------------------------------------ 
    #   Nacelles
    #------------------------------------------------------------------------------------------------------------------------------------ 
    nacelle                                     = RCAIDE.Library.Components.Nacelles.Stack_Nacelle()
    nacelle.tag                                 = 'nacelle_1'
    nacelle.length                              = 5
    nacelle.diameter                            = 0.85 
    nacelle.areas.wetted                        = 1.0   
    nacelle.origin                              = [[8.941625295,4.219315295, 1.616135105 ]]
    nacelle.flow_through                        = False     
         
    nac_segment                    = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                = 'segment_1'
    nac_segment.percent_x_location = 0.0 
    nac_segment.height             = 0.0
    nac_segment.width              = 0.0
    nacelle.append_segment(nac_segment)   
    
    nac_segment                    = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                = 'segment_2'
    nac_segment.percent_x_location = 0.2 /  nacelle.length
    nac_segment.percent_z_location = 0 
    nac_segment.height             = 0.4 
    nac_segment.width              = 0.4 
    nacelle.append_segment(nac_segment)   
    
    nac_segment                    = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                = 'segment_3'
    nac_segment.percent_x_location = 0.6 /  nacelle.length
    nac_segment.percent_z_location = 0 
    nac_segment.height             = 0.52 
    nac_segment.width              = 0.700 
    nacelle.append_segment(nac_segment)  
     
    nac_segment                    = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                = 'segment_4'
    nac_segment.percent_x_location = 0.754 /  nacelle.length
    nac_segment.percent_z_location = -0.16393 /  nacelle.length
    nac_segment.height             = 0.9	 
    nac_segment.width              = 0.85 
    nacelle.append_segment(nac_segment)  
    
    nac_segment                    = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                = 'segment_5'
    nac_segment.percent_x_location = 1.154  /  nacelle.length
    nac_segment.percent_z_location = -0.0819  /  nacelle.length
    nac_segment.height             = 0.8 
    nac_segment.width              = 0.85 
    nacelle.append_segment(nac_segment)   

    nac_segment                    = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                = 'segment_6'
    nac_segment.percent_x_location = 3.414   / nacelle.length
    nac_segment.percent_z_location = 0.08197  /  nacelle.length 
    nac_segment.height             = 0.6 
    nac_segment.width              = 0.85 
    nacelle.append_segment(nac_segment)
    

    nac_segment                    = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                = 'segment_6'
    nac_segment.percent_x_location = 0.96 
    nac_segment.percent_z_location = 0.08197  /  nacelle.length 
    nac_segment.height             = 0.3
    nac_segment.width              = 0.50
    nacelle.append_segment(nac_segment)    
    
    nac_segment                    = RCAIDE.Library.Components.Nacelles.Segment()
    nac_segment.tag                = 'segment_7'
    nac_segment.percent_x_location = 1.0 
    nac_segment.percent_z_location = 0 	
    nac_segment.height             = 0.001
    nac_segment.width              = 0.001  
    nacelle.append_segment(nac_segment) 
     
     
    starboard_propulsor.nacelle =  nacelle  
        
    fuel_line.propulsors.append(starboard_propulsor)
    

    #------------------------------------------------------------------------------------------------------------------------------------  
    # Port Propulsor
    #------------------------------------------------------------------------------------------------------------------------------------   
    port_propulsor                               = deepcopy(starboard_propulsor)
    port_propulsor.tag                           = "port_propulsor"
    port_propulsor.active_fuel_tanks             = ['fuel_tank']   

    port_propulsor.propeller                     = deepcopy(propeller)
    port_propulsor.propeller.tag                 = 'port_propeller' 
    port_propulsor.propeller.origin              = [[ 9.559106394 ,-4.219315295, 1.616135105]] 
    port_propulsor.propeller.clockwise_rotation  = False   
                
    port_propulsor.engine.origin                 = [[ 9.559106394 ,-4.219315295, 1.616135105]]   
    
 
    port_propulsor.nacelle.tag                   = 'nacelle_2'
    port_propulsor.nacelle.origin                = [[8.941625295,-4.219315295, 1.616135105 ]]    
    
    # append propulsor to distribution line 
    fuel_line.propulsors.append(port_propulsor) 

    net.fuel_lines.append(fuel_line)        

    #------------------------------------------------------------------------------------------------------------------------------------ 
    # Avionics
    #------------------------------------------------------------------------------------------------------------------------------------ 
    Wuav                                        = 2. * Units.lbs
    avionics                                    = RCAIDE.Library.Components.Systems.Avionics()
    avionics.mass_properties.uninstalled        = Wuav
    vehicle.avionics                            = avionics     

    #------------------------------------------------------------------------------------------------------------------------------------ 
    #   Vehicle Definition Complete
    #------------------------------------------------------------------------------------------------------------------------------------ 


    return vehicle